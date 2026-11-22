# Spec

How the program meets the requirements in `problem.md`. Updated each round.

## Round 1

### Shape of the code

| File | Holds | Tested |
|---|---|---|
| `tracker.py` | All rules: amounts, transactions, totals, budgets | Yes |
| `storage.py` | Reading and writing the local save file | Yes |
| `app.py` | HTTP routes and templates only | No — presentation |
| `templates/index.html` | The one page | No — presentation |
| `tests/` | One test file per module, each test named for a requirement ID | — |

The split is the point. `tracker.py` never opens a file, never prints, and never
imports Flask, so every rule can be checked by calling a function and looking at
what comes back. `app.py` holds no rules: it reads the form, calls `tracker`,
and renders.

### Money

Amounts are a whole number of **cents**, held in `int`, never a float.
`parse_amount` turns what someone typed (`12`, `12.3`, `12.34`, `$1,234.56`)
into cents and refuses anything else. `format_amount` turns cents back into
`1,234.56` for display. See
`docs/decisions/0001-money-as-integer-cents.md`.

### How each requirement is met

- **R1** — `Ledger.record(kind, amount, category, description, date)` builds a
  transaction through `make_transaction`, which is the only way one is made. It
  refuses an unknown kind, an amount that is not a positive number, and a date
  that is not on the calendar. `kind` is `"income"` or `"expense"`; the amount
  itself never carries a sign.
- **R2** — `CATEGORIES` is a fixed tuple of eight categories. Every transaction
  carries one, and `make_transaction` raises `ValueError` for anything not on
  the list, so a typo cannot create a silent ninth category.
- **R3** — `Ledger.in_order()` returns the transactions newest first. The sort
  is stable, so two entries on the same day stay in the order they were
  entered.
- **R4** — `total_income()`, `total_expenses()`, and `balance()`. Each takes an
  optional `month` (`"2026-11"`) to scope it. `balance()` is income minus
  expenses and may be negative.
- **R5** — `Ledger.set_budget(category, amount)` stores a monthly limit per
  category. A limit of zero is allowed and means "nothing here". Negative is
  refused, as is a category not on the list.
- **R6** — `Ledger.budget_report(month)` returns one `BudgetLine` per category
  that has a budget, in category order. Each line carries `limit`, `spent`,
  `remaining`, `percent_used`, and `is_over`. Only expenses in that category and
  that month count: income against a budgeted category does not reduce it.
- **R7** — `storage.save(ledger, path)` writes the whole ledger as JSON;
  `storage.load(path)` reads it back, returning an empty `Ledger` when the file
  does not exist yet. `app.py` loads at the start of a request and saves after a
  change, so closing the browser or stopping the program loses nothing.

### Worked example

Food budget `400.00`, then two expenses in November:

| | Amount | Cents |
|---|---|---|
| Budget | 400.00 | 40000 |
| Groceries | 150.25 | 15025 |
| Takeaway | 99.75 | 9975 |
| Spent | 250.00 | 25000 |
| Remaining | 150.00 | 15000 |

`percent_used` is `25000 / 40000 * 100` = `62.5`, and `is_over` is false. An
expense of `300.00` in Housing that same month changes none of this, because the
Food line only counts Food.

### Running it

    python3 app.py          # then open http://127.0.0.1:5000
    python3 -m pytest

### Out of scope in round 1

- More than one person, accounts, or logins.
- Any connection to a real bank, card, or payment service.
- Editing or deleting a transaction once recorded.
- Recurring transactions, transfers between categories, or multiple currencies.
- Charts, reports over several months, or exporting.
- Categories the person defines themselves.
