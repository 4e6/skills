import { test, expect, mock } from 'claude-code/testing'
import type { SessionMessage } from 'claude-code'

const TURN = { answer: 'ok', durationMs: 10, isAborted: false, turnId: 't', reason: 'answer' } as const
const USAGE = { input_tokens: 1, output_tokens: 1, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 }
const OBSERVER = '# Observer\n\nthe prompt'
const OBS = (category: string, line: string, involved = '') =>
  JSON.stringify({ category, line, evidence: [], quote: '', involved, count: 1 })

type Setup = {
  clock: ReturnType<typeof mock.clock>
  prompts: string[]
  blocks: unknown[]
  logs: { text: string; to: string }[]
  toasts: string[]
  state: { messages: SessionMessage[]; surfaces: string[]; reply: string; reads: number; file: string; model: (() => Promise<{ value: unknown }>) | undefined }
}

function setup(on: Parameters<Parameters<typeof test>[1]>[1], env: Record<string, string> = {}): Setup {
  const clock = mock.clock(on)
  mock.env(on, { SESSION_WATCH_IDLE_MS: '2000', SESSION_WATCH_EVERY: '1', ...env })
  const s: Setup = { clock, prompts: [], blocks: [], logs: [], toasts: [], state: { messages: [], surfaces: ['terminal'], reply: '', reads: 0, file: OBSERVER, model: undefined } }
  on('turn.complete', async (_$, e) => ({ text: e.answer }))
  on('session.start', async (_$, e) => ({ cwd: e.cwd }))
  on('session.end', async (_$, e) => ({ sessionId: e.sessionId }))
  on('turn.start', async (_$, e) => ({ turnId: e.turnId }))
  on('fs.read', async () => ({ value: s.state.file }))
  on('session.id', async () => ({ value: 'sess-1' }))
  on('session.surfaces', async () => ({ value: s.state.surfaces as never }))
  on('session.messages', async () => { s.state.reads += 1; return { value: s.state.messages } })
  on('model.complete', async (_$, e) => {
    s.prompts.push(e.prompt)
    if (s.state.model) return s.state.model() as never
    return { value: { isAnswered: true, text: s.state.reply, usage: USAGE } }
  })
  on('ui.log', async (_$, e) => { s.logs.push({ text: e.text, to: e.to }); return { value: undefined } })
  on('ui.toast', async (_$, e) => { s.toasts.push(e.text); return { value: undefined } })
  return s
}

const user = (text: string): SessionMessage => ({ role: 'user', text, toolUses: [] })
const asst = (text: string, uses: SessionMessage['toolUses'] = []): SessionMessage => ({ role: 'assistant', text, toolUses: uses })
const use = (id: string, tool: string, text?: string, isError?: true): SessionMessage['toolUses'][number] =>
  ({ tool_use_id: id, tool, input: { command: 'ls' }, ...(text !== undefined ? { text } : {}), ...(isError ? { isError } : {}) })

test('one check after idle, once, with the observer prompt and the slice', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('hello'), asst('hi')]
  await $.turn.complete(TURN)
  await s.clock.advance(1999)
  expect(s.prompts.length).toBe(0)
  await s.clock.advance(1)
  expect(s.prompts.length).toBe(1)
  await s.clock.advance(60000)
  expect(s.prompts.length).toBe(1)
  expect(s.prompts[0]).toContain('# Observer')
  expect(s.prompts[0]).toContain('slice of a live session')
  expect(s.prompts[0]).toMatch(/\[\d\d:\d\d\] USER: hello/)
})

test('the idle wait is clamped to 2000 ms', async ($, on) => {
  const s = setup(on, { SESSION_WATCH_IDLE_MS: '5' })
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(1999)
  expect(s.prompts.length).toBe(0)
  await s.clock.advance(1)
  expect(s.prompts.length).toBe(1)
})

test('a turn starting cancels the wait; the next turn arms it again', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(1500)
  await $.turn.start({ text: 'more', turnId: 't2' })
  await s.clock.advance(60000)
  expect(s.prompts.length).toBe(0)
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)
})

test('a subagent turn starts nothing', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('a')]
  await $.turn.complete({ ...TURN, agentId: 'a1' })
  await s.clock.advance(60000)
  expect(s.prompts.length).toBe(0)
})

test('headless: no surfaces, no model call, no messages read', async ($, on) => {
  const s = setup(on)
  s.state.surfaces = []
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(60000)
  expect(s.prompts.length).toBe(0)
  expect(s.state.reads).toBe(0)
  expect(s.logs.filter(l => l.text.includes('checked')).length).toBe(0)
})

test('a check is due after 3 turns, or 2 errored tool uses', async ($, on) => {
  const s = setup(on, { SESSION_WATCH_EVERY: '3' })
  s.state.messages = [user('a'), asst('b')]
  for (let i = 0; i < 2; i++) {
    await $.turn.complete(TURN)
    await s.clock.advance(2000)
  }
  expect(s.prompts.length).toBe(0)
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)

  // one error is not enough; the second makes a check due
  s.state.messages = [...s.state.messages, asst('', [use('e1', 'Bash', 'boom', true)])]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)
  s.state.messages = [...s.state.messages, asst('', [use('e2', 'Bash', 'boom', true)])]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(2)
})

test('a denied call appears as an errored tool use and counts as an error', async ($, on) => {
  const s = setup(on, { SESSION_WATCH_EVERY: '99' })
  s.state.messages = [
    user('go'),
    asst('', [use('d1', 'Bash', 'Permission to use Bash has been denied.', true)]),
    asst('', [use('d2', 'Edit', 'The user doesn\'t want to proceed with this tool use.', true)]),
  ]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)
  expect(s.prompts[0]).toContain('-> ERROR: Permission to use Bash has been denied.')
})

test('the renderer follows the observer grammar, cuts lines and caps the window', async ($, on) => {
  const s = setup(on)
  const long = 'x'.repeat(2000)
  s.state.messages = [
    user('fix it'),
    asst('looking', [use('t1', 'Read', 'content'), use('t2', 'Bash', long, true)]),
    { role: 'user', text: '', toolUses: [], toolResults: [{ tool_use_id: 't2', text: 'DUPLICATE-RESULT', isError: true, result: null } as never] },
  ]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  const p = s.prompts[0]!
  expect(p).toMatch(/\[\d\d:\d\d\] ASSISTANT: looking/)
  expect(p).toMatch(/TOOL Read#1: /)
  expect(p).toContain('  -> ok')
  expect(p).toMatch(/TOOL Bash#2: /)
  expect(p).toContain('  -> ERROR: ' + 'x'.repeat(600) + '…')
  expect(p).not.toContain('x'.repeat(601))
  expect(p).not.toContain('DUPLICATE-RESULT')
  expect(p).toContain('Session sess-1')

  // the cap keeps the newest lines
  const many: SessionMessage[] = []
  for (let i = 0; i < 40; i++) {
    const uses = []
    for (let j = 0; j < 10; j++) uses.push({ tool_use_id: `c${i}-${j}`, tool: `T${i}x${j}`, input: { v: 'y'.repeat(500) }, text: 'fine' })
    many.push(asst('', uses))
  }
  s.state.messages = many
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  const q = s.prompts[1]!
  expect(q.length < OBSERVER.length + 24000 + 400).toBe(true)
  expect(q.includes('TOOL T39x9#400')).toBe(true)
  expect(q.includes('TOOL T0x0#1:')).toBe(false)
})

test('the cursor: only what is new after the last tool use is sent', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('first'), asst('', [use('a1', 'Bash', 'ok')]), user('second-ask')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts[0]).toContain('first')
  s.state.messages = [...s.state.messages, asst('third-reply'), user('fourth')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  const q = s.prompts[1]!
  expect(q).toContain('third-reply')
  expect(q).toContain('fourth')
  expect(q).not.toContain('first')
  expect(q).not.toContain('second-ask')
})

test('the cursor: an anchor not found falls back to the last 40 entries', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('old'), asst('', [use('gone', 'Bash', 'ok')])]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  const next: SessionMessage[] = []
  for (let i = 0; i < 60; i++) next.push(user(`m${i}`))
  s.state.messages = next
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  const q = s.prompts[1]!
  expect(q).toContain('m59')
  expect(q).toContain('m20')
  expect(q).not.toContain('m19 ')
  expect(q).not.toMatch(/USER: m19$/m)
})

test('a /clear resets the cursor', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('before'), asst('', [use('a1', 'Bash', 'ok')])]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  await $.session.end({ reason: 'clear', sessionId: 'sess-1', resume: {} as never })
  s.state.messages = [user('after-clear')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts[1]).toContain('after-clear')
})

test('the guard: a file that is not the observer means no check', async ($, on) => {
  const s = setup(on)
  s.state.file = 'not the prompt'
  s.state.messages = [user('a')]
  await $.session.start({ cwd: '/x', surface: 'terminal', isInteractive: true })
  await $.turn.complete(TURN)
  await s.clock.advance(60000)
  expect(s.prompts.length).toBe(0)
  expect(s.logs.filter(l => l.to === 'debug' && l.text.includes('missing or not the observer prompt')).length).toBe(1)
})

test('output parsing ignores junk lines', async ($, on) => {
  const s = setup(on)
  s.state.reply = ['Here you go:', '{broken', OBS('circling', 'tried twice'), '[1,2]', '{"category":1}', ''].join('\n')
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  const visible = s.logs.filter(l => l.to === 'transcript')
  expect(visible.map(l => l.text)).toEqual(['session-watch: circling: tried twice'])
})

test('every check writes the debug line; a first occurrence logs, a repeat toasts, an identical line is not shown twice', async ($, on) => {
  const s = setup(on)
  s.state.messages = [user('a')]
  s.state.reply = OBS('permission', 'denied Bash', 'Bash')
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.logs).toContainEqual({ text: 'session-watch: checked 1 msgs, 1 observations', to: 'debug' })
  expect(s.logs.filter(l => l.to === 'transcript').length).toBe(1)
  expect(s.toasts.length).toBe(0)

  s.state.messages = [...s.state.messages, user('b')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.logs.filter(l => l.to === 'transcript').length).toBe(1) // identical line
  expect(s.toasts.length).toBe(0)

  s.state.reply = OBS('permission', 'denied Edit as well', 'Bash')
  s.state.messages = [...s.state.messages, user('c')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.logs.filter(l => l.to === 'transcript').length).toBe(2)
  expect(s.toasts).toEqual(['session-watch: permission: denied Edit as well'])
  expect(s.logs.filter(l => l.text.startsWith('session-watch: checked')).length).toBe(3)
})

test('no second call while one is in flight', async ($, on) => {
  const s = setup(on)
  let release: () => void = () => undefined
  s.state.model = async () => {
    await new Promise<void>(r => { release = r })
    return { value: { isAnswered: false, reason: 'empty-reply', usage: USAGE } }
  }
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)
  release()
  await s.clock.advance(1)
})

test('a failing model call stays silent and the session goes on', async ($, on) => {
  const s = setup(on)
  s.state.model = async () => { throw new Error('model blocked') }
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.logs.filter(l => l.to === 'transcript').length).toBe(0)
  expect(s.toasts.length).toBe(0)
})

test('the test knob adds one fixed observation after the real call, once', async ($, on) => {
  const s = setup(on, { SESSION_WATCH_TEST_OBSERVATION: '1' })
  s.state.messages = [user('a')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.prompts.length).toBe(1)
  const shown = s.logs.filter(l => l.to === 'transcript').map(l => l.text)
  expect(shown.length).toBe(1)
  expect(shown[0]).toContain('swtest-marker-Q7X')
  s.state.messages = [...s.state.messages, user('b')]
  await $.turn.complete(TURN)
  await s.clock.advance(2000)
  expect(s.logs.filter(l => l.to === 'transcript').length).toBe(1)
})
