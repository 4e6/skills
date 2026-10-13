import type { Register, EngineInterface, Timer, SessionMessage } from 'claude-code'

// Quiet time after a main-loop turn before the watcher looks. A turn starting
// cancels the wait, so a check never runs while the session works.
const IDLE_MS = 20_000
// A check is due when this many main-loop turns have passed since the last one...
const EVERY_TURNS = 3
// ...or this many errored tool uses (a refused or denied call counts) are in the new part.
const EVERY_ERRORS = 2
// The least a test may set the idle wait to, and the least turns a check may wait for.
const MIN_IDLE_MS = 2000
const MIN_EVERY = 1
// The most conversation entries one check reads.
const MAX_ENTRIES = 40
// Cuts of one rendered line, in characters.
const TEXT_CUT = 300
const ERROR_CUT = 600
// The whole window sent to the model, in characters; the oldest lines go first.
const WINDOW_CAP = 24_000
// The cheapest model, the reply cap and the time limit of the one call a check makes.
const MODEL = 'haiku'
const MAX_TOKENS = 600
const TIMEOUT_MS = 30_000
// The prompt file must open with this, or the link did not resolve to the observer.
const GUARD = '# Observer'
// Starts every line shown to the user: ASCII, so it can be searched for.
const MARKER = 'session-watch:'
// One fixed observation, drawn after the real call when SESSION_WATCH_TEST_OBSERVATION=1.
const TEST_LINE =
  '{"category":"environment","line":"swtest-marker-Q7X drawn by the test knob","evidence":[],"quote":"","involved":"swtest","count":1}'
const LIVE_NOTE =
  'This is a slice of a live session, not a whole one. Messages carry no time; every line is stamped with the time of this check.'

let turns = 0
let timer: Timer | undefined
let inFlight = false
let observer: string | undefined
let guardLogged = false
let anchor: { id: string; after: number } | undefined
let testPending = true
const shown = new Set<string>()
const keysSeen = new Set<string>()

type Observation = { category: string; line: string; involved: string }

function cut(text: string, n: number): string {
  const one = text.replace(/\s+/g, ' ').trim()
  return one.length > n ? `${one.slice(0, n)}…` : one
}

function clock(ms: number): string {
  const d = new Date(ms)
  const two = (v: number) => String(v).padStart(2, '0')
  return `[${two(d.getHours())}:${two(d.getMinutes())}]`
}

// The conversation slice as the observer's record. Outcomes come from the tool
// uses alone; a user message holding only tool results adds no line (it would count twice).
function render(sessionId: string, msgs: readonly SessionMessage[], now: number): string {
  const stamp = clock(now)
  const lines: string[] = []
  let n = 0
  for (const m of msgs) {
    if (m.text.trim() !== '') lines.push(`${stamp} ${m.role === 'user' ? 'USER' : 'ASSISTANT'}: ${cut(m.text, TEXT_CUT)}`)
    for (const u of m.toolUses) {
      n += 1
      lines.push(`${stamp} TOOL ${u.tool}#${n}: ${cut(JSON.stringify(u.input) ?? '', TEXT_CUT)}`)
      if (u.isError === true) lines.push(`  -> ERROR: ${cut(u.text ?? '', ERROR_CUT)}`)
      else if (u.text !== undefined || u.result !== undefined) lines.push('  -> ok')
      else lines.push('  -> (no result recorded)')
    }
  }
  let total = 0
  let from = lines.length
  while (from > 0 && total + lines[from - 1]!.length + 1 <= WINDOW_CAP) {
    from -= 1
    total += lines[from]!.length + 1
  }
  return `Session ${sessionId} (slice of a live session)\n${LIVE_NOTE}\n\n${lines.slice(from).join('\n')}`
}

function parse(reply: string): Observation[] {
  const out: Observation[] = []
  for (const raw of reply.split('\n')) {
    const t = raw.trim()
    if (!t.startsWith('{')) continue
    try {
      const o = JSON.parse(t) as Record<string, unknown>
      if (typeof o.category === 'string' && typeof o.line === 'string' && o.category !== '' && o.line !== '') {
        out.push({ category: o.category, line: o.line, involved: typeof o.involved === 'string' ? o.involved : '' })
      }
    } catch {
      // not an observation
    }
  }
  return out
}

// Where the new part starts: after the last tool use seen at the previous check
// plus the messages seen after it. Not found, or never anchored: the last MAX_ENTRIES.
function start(all: readonly SessionMessage[]): number {
  const fallback = Math.max(0, all.length - MAX_ENTRIES)
  if (anchor === undefined) return fallback
  for (let i = all.length - 1; i >= 0; i--) {
    if (all[i]!.toolUses.some(u => u.tool_use_id === anchor!.id)) {
      return Math.max(i + 1 + anchor.after, fallback)
    }
  }
  return fallback
}

function reanchor(all: readonly SessionMessage[]): void {
  for (let i = all.length - 1; i >= 0; i--) {
    const uses = all[i]!.toolUses
    if (uses.length > 0) {
      anchor = { id: uses[uses.length - 1]!.tool_use_id, after: all.length - 1 - i }
      return
    }
  }
  anchor = undefined
}

function errors(msgs: readonly SessionMessage[]): number {
  return msgs.reduce((a, m) => a + m.toolUses.filter(u => u.isError === true).length, 0)
}

async function number($: EngineInterface, name: 'idle' | 'every'): Promise<number> {
  const raw = name === 'idle' ? await $.env.get('SESSION_WATCH_IDLE_MS') : await $.env.get('SESSION_WATCH_EVERY')
  const v = Number(raw)
  if (raw === undefined || raw === '' || !Number.isFinite(v)) return name === 'idle' ? IDLE_MS : EVERY_TURNS
  return name === 'idle' ? Math.max(MIN_IDLE_MS, v) : Math.max(MIN_EVERY, Math.floor(v))
}

async function loadObserver($: EngineInterface): Promise<boolean> {
  if (observer === undefined) {
    let text = ''
    try {
      text = await $.fs.read(`${$.plugin.root}/observer.md`)
    } catch {
      text = ''
    }
    observer = text.startsWith(GUARD) ? text : ''
  }
  if (!guardLogged) {
    guardLogged = true
    $.ui.log(
      observer !== ''
        ? `session-watch: observer.md read OK (${observer.length} chars)`
        : 'session-watch: observer.md missing or not the observer prompt; no checks this session',
      { to: 'debug' },
    )
  }
  return observer !== ''
}

function surface($: EngineInterface, found: Observation[]): void {
  const fresh = new Set<string>()
  for (const o of found) {
    const text = `${MARKER} ${o.category}: ${o.line}`
    if (shown.has(text)) continue
    shown.add(text)
    const key = `${o.category}|${o.involved}`
    const repeat = keysSeen.has(key)
    fresh.add(key)
    $.ui.log(text)
    if (repeat) $.ui.toast(text)
  }
  for (const k of fresh) keysSeen.add(k)
}

async function check($: EngineInterface): Promise<void> {
  if (inFlight) return
  try {
    if ((await $.session.surfaces()).length === 0) return
    if (!(await loadObserver($))) return
    const all = await $.session.messages()
    const win = all.slice(start(all))
    const every = await number($, 'every')
    if (turns < every && errors(win) < EVERY_ERRORS) return
    inFlight = true
    turns = 0
    reanchor(all)
    const observations: Observation[] = []
    if (win.length > 0) {
      let id = 'unknown'
      try {
        id = await $.session.id()
      } catch {
        id = 'unknown'
      }
      const r = await $.model.complete({
        model: MODEL,
        prompt: [
          { text: observer!, cache: true },
          { text: render(id, win, await $.clock.now()) },
        ],
        maxTokens: MAX_TOKENS,
        timeoutMs: TIMEOUT_MS,
      })
      if (r.isAnswered) observations.push(...parse(r.text))
    }
    if (testPending && (await $.env.get('SESSION_WATCH_TEST_OBSERVATION')) === '1') {
      testPending = false
      observations.push(...parse(TEST_LINE))
    }
    $.ui.log(`session-watch: checked ${win.length} msgs, ${observations.length} observations`, { to: 'debug' })
    surface($, observations)
  } catch {
    // The session may be gone, the model blocked, the call slow: stay silent.
  } finally {
    inFlight = false
  }
}

async function arm($: EngineInterface): Promise<void> {
  const ms = await number($, 'idle')
  timer?.cancel()
  timer = $.clock.after(ms, () => {
    timer = undefined
    void check($)
  })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    try {
      await loadObserver($)
    } catch {
      // stay silent
    }
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) {
      turns += 1
      await arm($)
    }
    return next(e)
  })

  on('turn.start', ($, e, next) => {
    timer?.cancel()
    timer = undefined
    return next(e)
  })

  on('session.end', ($, e, next) => {
    if (e.reason === 'clear') {
      timer?.cancel()
      timer = undefined
      turns = 0
      anchor = undefined
    }
    return next(e)
  })
}
