You are grading one run of an assistant that used a meal-planning skill. An
endurance athlete described their week in one message, and the assistant wrote
a week of meals as JSON and replied to them. Answer each question below about
this run.

- Answer `yes`, `no` or `unclear`, with one sentence of reason that quotes the
  plan or the reply where it can.
- `unclear` only where what you were given cannot settle the question, never to
  avoid a hard call.
- Judge what is written, not what the assistant may have meant. Do not reward
  length, tone or effort.
- `week_load` in the plan is the assistant's own working and is never shown to
  the athlete; everything else in the plan is printed on their page.

## What the athlete said

<athlete>
{message}
</athlete>

## The plan the assistant wrote

<plan>
{plan}
</plan>

## The assistant's last reply to the athlete

<reply>
{reply}
</reply>

## Questions

{questions}
