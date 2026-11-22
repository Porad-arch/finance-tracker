# finance-tracker

A local personal finance tracker with a small web interface. Standing rules for
every session in this repo.

## Read these first

`problem.md` (the problem and the numbered requirements), `spec.md` (how the code
meets them), `docs/decisions/` (why things are the way they are), and the newest
`handoff-round-<N>.md` if one exists.

## Commands

    python3 app.py         # run the web app, then open http://127.0.0.1:5000
    python3 -m pytest      # run the tests

## How this repo works

- **Requirements come first.** `problem.md` holds numbered requirements R1, R2,
  … Numbers are never reused. A changed requirement keeps its number and says
  what changed; a removed one stays in the file, marked removed.
- **Rules are separate from the web layer and from storage.** Everything
  testable lives in `tracker.py` as pure functions and plain state. `storage.py`
  only reads and writes the save file. `app.py` only handles HTTP and templates.
  Do not put a rule in `app.py`.
- **Money is stored as a whole number of cents**, never as a float. See
  `docs/decisions/0001-money-as-integer-cents.md`.
- **Every requirement is named in a test.** Test names start with the
  requirement ID, for example `test_r4_...`. When a requirement changes, its
  tests change with it in the same round.
- **Tests must actually run.** A skipped test has not passed. Nothing may be
  added that cannot run with `python3 -m pytest`.
- **No real financial data, ever.** This is a course project. The save file is
  local, there are no accounts, no bank connections, and no network calls. Use
  made-up figures when trying it out.
- **No API keys, no logins, no paid services.**

## Commits

- Small steps, one change per commit.
- The message says what changed and why. Never `update`, `fix`, or `wip`.
- **Never undo or amend a commit**, and never force-push.
- Push at the end of each working session.

## Never commit

`data.json` or any save file, transcripts (`.jsonl`), API keys or passwords,
`.venv`, `__pycache__`, `node_modules`, or personal information. This repository
is public.

## Each round

Requirements into `problem.md` first and pushed before anything else. Then
update `spec.md`, write tests for every new or changed requirement, implement
until all tests pass including the old ones, and add a decision record in
`docs/decisions/` as a Y-statement for a decision that had real alternatives.
