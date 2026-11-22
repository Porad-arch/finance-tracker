# 0001. Money is a whole number of cents

Date: 2026-11-21

## Status

Accepted.

## Decision

In the context of **storing and adding up amounts of money**,
facing **the fact that binary floating point cannot represent most decimal
amounts exactly**,
we decided for **holding every amount as a Python `int` counting cents**, with
`parse_amount` converting what someone typed on the way in and `format_amount`
converting back on the way out,
and neglected **`float`** and **`decimal.Decimal`**,
to achieve **totals that are exactly right and a save file that cannot drift**,
accepting **that every amount has to be converted at the edges, and that the
numbers in `data.json` are cents rather than the dollars a reader might expect**.

## Why not float

`float` is the obvious choice and it is wrong for money. In Python:

    >>> 0.1 + 0.2
    0.30000000000000004
    >>> 0.1 + 0.2 == 0.3
    False

Sum a few hundred expenses and the error is visible in the total. A budget page
that says you have `-0.00` left, or `99.99999999` percent used, is a bug the
person cannot do anything about. `tests/test_tracker.py` keeps this honest:
`test_r1_amounts_are_cents_so_decimals_do_not_drift` asserts both that
`0.1 + 0.2 != 0.3` in floating point and that the same two amounts recorded as
cents total exactly `30`.

## Why not Decimal

`decimal.Decimal` is exact and is the right answer in a larger program. It was
rejected here for two smaller reasons: it does not serialise to JSON without a
custom encoder, which would put a conversion step in `storage.py` as well as at
the edges, and every comparison in a test would have to be written
`Decimal("12.34")` instead of `1234`. For a single-user tracker, `int` cents is
exact, needs no library, and reads plainly in both the tests and the save file.

## Consequences

- `Transaction.amount` and the values in `Ledger.budgets` are always `int`
  cents, and always positive. Whether money came in or went out is the
  transaction's `kind`, never the sign of its amount.
- Conversion happens only at the edges: `parse_amount` on input,
  `format_amount` (as the `money` filter) in the template.
- `percent_used` is the one deliberate float in the program, because it is a
  ratio for display and never gets added to anything.
- If a future round needs a currency other than dollars, the unit stops being
  "cents" and this record will need revisiting.
