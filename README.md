# finance-tracker

A small personal finance tracker that runs on your own computer. Record what
comes in and what goes out, tag each one with a category, set a monthly budget
per category, and see at a glance how much of each budget is gone.

Everything is saved to a plain JSON file next to the program. There are no
accounts, no sign-in, no bank connection, and no network calls. **It is a course
project: use made-up figures, not your real finances.**

## Run it

    python3 app.py

Then open <http://127.0.0.1:5000> in a browser. `127.0.0.1` means this machine
only, so nothing on the network can reach it.

Requires Python 3 and Flask (`python3 -m pip install flask`).

To try it out without touching your own save file, point it somewhere else:

    FINANCE_TRACKER_DATA=/tmp/demo.json python3 app.py

## Run the tests

    python3 -m pytest

44 tests, each named for the requirement it checks, so a failure tells you which
requirement in `problem.md` is no longer met. Requires `pytest`
(`python3 -m pip install pytest`).

## What it does

| | |
|---|---|
| Record | An income or an expense, with an amount, category, description, and date |
| Categories | Housing, Food, Transport, Utilities, Health, Entertainment, Savings, Other |
| Totals | Income, expenses, and balance, for the month shown and across all months |
| Budgets | A monthly limit per category, with spent, left, and percent used |
| Saving | A JSON file, written whenever something changes |

Amounts can be typed as `12`, `12.5`, `12.34`, or `$1,234.56`. Anything else is
refused with a message instead of being guessed at.

## How it is laid out

- `tracker.py` — the rules: amounts, transactions, totals, budgets. No file
  access, no printing, no Flask.
- `storage.py` — the only file that touches the disk.
- `app.py` — the web layer: routes and forms, no rules.
- `templates/index.html` — the one page.
- `tests/` — one test file per module; each test is named for the requirement
  it checks.
- `problem.md` — who this is for and the numbered requirements.
- `spec.md` — how the code meets them.
- `docs/decisions/` — why things are the way they are.

## One thing worth knowing

Money is stored as a whole number of **cents**, never a float, because
`0.1 + 0.2` is not `0.3` in floating point and those errors pile up in a total.
So `12.34` is held as `1234`, which is also what you will see in `data.json`.
The reasoning is in
[docs/decisions/0001-money-as-integer-cents.md](docs/decisions/0001-money-as-integer-cents.md).
