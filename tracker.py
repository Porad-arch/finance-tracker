"""The rules: transactions, totals, and budgets.

Nothing in this file reads input, prints, touches the network, or opens a file.
Every rule is a function or a plain object you can call from a test and look at
what comes back. The web layer lives in app.py and the save file in storage.py.

Money is always a whole number of cents, never a float. See
docs/decisions/0001-money-as-integer-cents.md for why.
"""

import re
from dataclasses import dataclass, field
from datetime import date as _date

INCOME = "income"
EXPENSE = "expense"
KINDS = (INCOME, EXPENSE)

CATEGORIES = (
    "Housing",
    "Food",
    "Transport",
    "Utilities",
    "Health",
    "Entertainment",
    "Savings",
    "Other",
)

# One or more digits, optionally a decimal point and one or two more digits.
_AMOUNT = re.compile(r"\d+(\.\d{1,2})?")


def today():
    """Today as YYYY-MM-DD."""
    return _date.today().isoformat()


def parse_amount(text, allow_zero=False):
    """Turn typed money such as '12.34' or '$1,234.56' into cents.

    Returns a positive whole number of cents. Raises ValueError with a message
    meant for the person who typed it. The amount never carries a sign: whether
    something is income or an expense is the transaction's kind, not its number.
    """
    if isinstance(text, int):
        cents = text
    else:
        cleaned = str(text).strip().replace(",", "").lstrip("$").strip()
        if not cleaned:
            raise ValueError("enter an amount")
        if not _AMOUNT.fullmatch(cleaned):
            raise ValueError(f"{cleaned!r} is not an amount like 12 or 12.34")
        whole, _, frac = cleaned.partition(".")
        cents = int(whole) * 100 + int(frac.ljust(2, "0") or 0)
    if cents < 0:
        raise ValueError("the amount cannot be negative")
    if cents == 0 and not allow_zero:
        raise ValueError("the amount must be more than zero")
    return cents


def format_amount(cents):
    """Cents back into something readable: 123456 -> '1,234.56'."""
    sign = "-" if cents < 0 else ""
    cents = abs(int(cents))
    return f"{sign}{cents // 100:,}.{cents % 100:02d}"


@dataclass(frozen=True)
class Transaction:
    """One recorded piece of money. The amount is positive cents."""

    kind: str
    amount: int
    category: str
    description: str = ""
    date: str = ""

    @property
    def month(self):
        """The YYYY-MM this falls in."""
        return self.date[:7]

    @property
    def signed_amount(self):
        """Positive for income, negative for an expense."""
        return self.amount if self.kind == INCOME else -self.amount


def make_transaction(kind, amount, category, description="", date=None):
    """Build a valid Transaction or raise ValueError saying what was wrong.

    This is the only way a Transaction should be made, so every one of them is
    already checked: a known kind, a positive amount, a known category, and a
    real calendar date.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be {INCOME!r} or {EXPENSE!r}, not {kind!r}")
    cents = parse_amount(amount)
    if category not in CATEGORIES:
        raise ValueError(f"{category!r} is not one of the categories")
    date = today() if date in (None, "") else str(date).strip()
    try:
        _date.fromisoformat(date)
    except ValueError:
        raise ValueError(f"{date!r} is not a date like 2026-11-21") from None
    return Transaction(
        kind=kind,
        amount=cents,
        category=category,
        description=" ".join(str(description).split()),
        date=date,
    )


@dataclass(frozen=True)
class BudgetLine:
    """How one category is doing against its budget for a month."""

    category: str
    limit: int
    spent: int

    @property
    def remaining(self):
        """What is left. Negative means over budget."""
        return self.limit - self.spent

    @property
    def percent_used(self):
        """How much of the budget is used, rounded to one decimal place.

        A budget of zero is a special case: anything spent against it is 100%
        used, because there was never any room.
        """
        if self.limit == 0:
            return 100.0 if self.spent > 0 else 0.0
        return round(self.spent / self.limit * 100, 1)

    @property
    def is_over(self):
        return self.spent > self.limit


@dataclass
class Ledger:
    """Everything recorded so far, plus the monthly budget for each category."""

    transactions: list = field(default_factory=list)
    budgets: dict = field(default_factory=dict)

    # --- recording (R1, R2) ---

    def add(self, transaction):
        self.transactions.append(transaction)
        return transaction

    def record(self, kind, amount, category, description="", date=None):
        """Validate and store one transaction. Returns the stored Transaction."""
        return self.add(make_transaction(kind, amount, category, description, date))

    # --- listing (R3) ---

    def in_order(self):
        """Newest first. Transactions on the same day keep the order entered."""
        return sorted(self.transactions, key=lambda t: t.date, reverse=True)

    def for_month(self, month=None):
        """Transactions in one YYYY-MM, or all of them when month is None."""
        if month is None:
            return list(self.transactions)
        return [t for t in self.transactions if t.month == month]

    # --- totals (R4) ---

    def total_income(self, month=None):
        return sum(t.amount for t in self.for_month(month) if t.kind == INCOME)

    def total_expenses(self, month=None):
        return sum(t.amount for t in self.for_month(month) if t.kind == EXPENSE)

    def balance(self, month=None):
        """Income minus expenses. Negative means more went out than came in."""
        return self.total_income(month) - self.total_expenses(month)

    # --- budgets (R5, R6) ---

    def set_budget(self, category, amount):
        """Set the monthly limit for one category. Zero is allowed."""
        if category not in CATEGORIES:
            raise ValueError(f"{category!r} is not one of the categories")
        self.budgets[category] = parse_amount(amount, allow_zero=True)
        return self.budgets[category]

    def spent_in(self, category, month=None):
        """Total spent in one category, for a month or over all time."""
        return sum(
            t.amount
            for t in self.for_month(month)
            if t.kind == EXPENSE and t.category == category
        )

    def budget_report(self, month=None):
        """One BudgetLine per category that has a budget, in category order."""
        return [
            BudgetLine(category, self.budgets[category], self.spent_in(category, month))
            for category in CATEGORIES
            if category in self.budgets
        ]
