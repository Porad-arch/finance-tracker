"""Tests for the rules in tracker.py.

Each test name begins with the requirement it checks, so a failure points
straight at the requirement in problem.md that is no longer met.
"""

import pytest

from tracker import (
    CATEGORIES,
    EXPENSE,
    INCOME,
    BudgetLine,
    Ledger,
    format_amount,
    make_transaction,
    parse_amount,
    today,
)

# --- R1. Allow users to record income and expenses. ---


def test_r1_records_an_income():
    ledger = Ledger()
    txn = ledger.record(INCOME, "2500.00", "Other", "paycheck", "2026-11-01")
    assert ledger.transactions == [txn]
    assert txn.kind == INCOME
    assert txn.amount == 250000


def test_r1_records_an_expense():
    ledger = Ledger()
    txn = ledger.record(EXPENSE, "45.50", "Food", "groceries", "2026-11-03")
    assert ledger.transactions == [txn]
    assert txn.kind == EXPENSE
    assert txn.amount == 4550


def test_r1_rejects_an_amount_that_is_not_a_number():
    with pytest.raises(ValueError):
        make_transaction(EXPENSE, "lots", "Food")


def test_r1_rejects_zero_and_negative_amounts():
    with pytest.raises(ValueError):
        make_transaction(EXPENSE, "0", "Food")
    with pytest.raises(ValueError):
        make_transaction(EXPENSE, "-5.00", "Food")


def test_r1_rejects_an_unknown_kind():
    with pytest.raises(ValueError):
        make_transaction("refund", "5.00", "Food")


def test_r1_defaults_the_date_to_today():
    assert make_transaction(INCOME, "10.00", "Other").date == today()


def test_r1_rejects_a_date_that_is_not_on_the_calendar():
    with pytest.raises(ValueError):
        make_transaction(EXPENSE, "10.00", "Food", date="2026-02-30")


def test_r1_amounts_are_cents_so_decimals_do_not_drift():
    # 0.1 + 0.2 != 0.3 in floating point. In cents it is just 10 + 20 == 30.
    assert 0.1 + 0.2 != 0.3
    ledger = Ledger()
    ledger.record(EXPENSE, "0.10", "Food", date="2026-11-01")
    ledger.record(EXPENSE, "0.20", "Food", date="2026-11-01")
    assert ledger.total_expenses() == 30
    assert format_amount(ledger.total_expenses()) == "0.30"


def test_r1_reads_money_written_several_ways():
    assert parse_amount("12") == 1200
    assert parse_amount("12.3") == 1230
    assert parse_amount("12.34") == 1234
    assert parse_amount("$1,234.56") == 123456
    assert parse_amount("0.05") == 5


# --- R2. Allow users to categorize transactions. ---


def test_r2_a_transaction_keeps_its_category():
    txn = make_transaction(EXPENSE, "20.00", "Transport", date="2026-11-04")
    assert txn.category == "Transport"


def test_r2_rejects_a_category_that_is_not_on_the_list():
    with pytest.raises(ValueError):
        make_transaction(EXPENSE, "20.00", "Yachts")


def test_r2_every_offered_category_can_be_used():
    for category in CATEGORIES:
        txn = make_transaction(EXPENSE, "1.00", category, date="2026-11-04")
        assert txn.category == category


# --- R3. Display a list of recorded transactions. ---


def test_r3_lists_every_recorded_transaction():
    ledger = Ledger()
    ledger.record(INCOME, "10.00", "Other", date="2026-11-01")
    ledger.record(EXPENSE, "4.00", "Food", date="2026-11-02")
    assert len(ledger.in_order()) == 2


def test_r3_lists_newest_first():
    ledger = Ledger()
    oldest = ledger.record(EXPENSE, "1.00", "Food", date="2026-11-01")
    newest = ledger.record(EXPENSE, "2.00", "Food", date="2026-11-20")
    middle = ledger.record(EXPENSE, "3.00", "Food", date="2026-11-10")
    assert ledger.in_order() == [newest, middle, oldest]


def test_r3_same_day_transactions_keep_the_order_entered():
    ledger = Ledger()
    first = ledger.record(EXPENSE, "1.00", "Food", "first", "2026-11-05")
    second = ledger.record(EXPENSE, "2.00", "Food", "second", "2026-11-05")
    later = ledger.record(EXPENSE, "3.00", "Food", "later", "2026-11-09")
    assert ledger.in_order() == [later, first, second]


def test_r3_an_empty_ledger_lists_nothing():
    assert Ledger().in_order() == []


# --- R4. Calculate total income, expenses, and remaining balance. ---


def test_r4_totals_income_and_expenses_and_balance():
    ledger = Ledger()
    ledger.record(INCOME, "2500.00", "Other", date="2026-11-01")
    ledger.record(EXPENSE, "800.00", "Housing", date="2026-11-02")
    ledger.record(EXPENSE, "45.50", "Food", date="2026-11-03")
    assert ledger.total_income() == 250000
    assert ledger.total_expenses() == 84550
    assert ledger.balance() == 165450
    assert format_amount(ledger.balance()) == "1,654.50"


def test_r4_balance_can_go_negative():
    ledger = Ledger()
    ledger.record(INCOME, "100.00", "Other", date="2026-11-01")
    ledger.record(EXPENSE, "150.00", "Food", date="2026-11-02")
    assert ledger.balance() == -5000
    assert format_amount(ledger.balance()) == "-50.00"


def test_r4_an_empty_ledger_totals_zero():
    ledger = Ledger()
    assert (ledger.total_income(), ledger.total_expenses(), ledger.balance()) == (0, 0, 0)


def test_r4_income_is_positive_and_an_expense_is_negative():
    assert make_transaction(INCOME, "10.00", "Other").signed_amount == 1000
    assert make_transaction(EXPENSE, "10.00", "Food").signed_amount == -1000


def test_r4_totals_can_be_scoped_to_one_month():
    ledger = Ledger()
    ledger.record(INCOME, "100.00", "Other", date="2026-10-15")
    ledger.record(INCOME, "200.00", "Other", date="2026-11-15")
    assert ledger.total_income("2026-11") == 20000
    assert ledger.total_income("2026-10") == 10000
    assert ledger.total_income() == 30000


# --- R5. Allow users to set monthly spending budgets by category. ---


def test_r5_sets_a_budget_for_a_category():
    ledger = Ledger()
    ledger.set_budget("Food", "400.00")
    assert ledger.budgets == {"Food": 40000}


def test_r5_a_budget_can_be_changed():
    ledger = Ledger()
    ledger.set_budget("Food", "400.00")
    ledger.set_budget("Food", "250.00")
    assert ledger.budgets == {"Food": 25000}


def test_r5_a_budget_of_zero_is_allowed():
    ledger = Ledger()
    ledger.set_budget("Entertainment", "0")
    assert ledger.budgets == {"Entertainment": 0}


def test_r5_rejects_a_budget_for_a_category_that_is_not_on_the_list():
    with pytest.raises(ValueError):
        Ledger().set_budget("Yachts", "400.00")


def test_r5_rejects_a_negative_budget():
    with pytest.raises(ValueError):
        Ledger().set_budget("Food", "-10.00")


# --- R6. Display how much of each budget has been used. ---


def test_r6_reports_spent_and_remaining_and_percent():
    ledger = Ledger()
    ledger.set_budget("Food", "400.00")
    ledger.record(EXPENSE, "150.25", "Food", date="2026-11-05")
    ledger.record(EXPENSE, "99.75", "Food", date="2026-11-06")
    (line,) = ledger.budget_report("2026-11")
    assert line.category == "Food"
    assert line.limit == 40000
    assert line.spent == 25000
    assert line.remaining == 15000
    assert line.percent_used == 62.5
    assert line.is_over is False


def test_r6_flags_a_category_that_is_over_budget():
    ledger = Ledger()
    ledger.set_budget("Entertainment", "100.00")
    ledger.record(EXPENSE, "120.00", "Entertainment", date="2026-11-07")
    (line,) = ledger.budget_report("2026-11")
    assert line.remaining == -2000
    assert line.percent_used == 120.0
    assert line.is_over is True


def test_r6_only_counts_spending_in_that_category():
    ledger = Ledger()
    ledger.set_budget("Food", "400.00")
    ledger.record(EXPENSE, "50.00", "Food", date="2026-11-05")
    ledger.record(EXPENSE, "300.00", "Housing", date="2026-11-05")
    (line,) = ledger.budget_report("2026-11")
    assert line.spent == 5000


def test_r6_only_counts_the_month_asked_for():
    ledger = Ledger()
    ledger.set_budget("Food", "100.00")
    ledger.record(EXPENSE, "80.00", "Food", date="2026-10-20")
    ledger.record(EXPENSE, "30.00", "Food", date="2026-11-20")
    assert ledger.budget_report("2026-11")[0].spent == 3000
    assert ledger.budget_report("2026-10")[0].spent == 8000
    assert ledger.budget_report()[0].spent == 11000


def test_r6_income_does_not_count_against_a_budget():
    ledger = Ledger()
    ledger.set_budget("Other", "100.00")
    ledger.record(INCOME, "500.00", "Other", date="2026-11-08")
    (line,) = ledger.budget_report("2026-11")
    assert line.spent == 0
    assert line.percent_used == 0.0
    assert line.is_over is False


def test_r6_reports_only_categories_that_have_a_budget_in_category_order():
    ledger = Ledger()
    ledger.set_budget("Savings", "50.00")
    ledger.set_budget("Food", "50.00")
    assert [line.category for line in ledger.budget_report()] == ["Food", "Savings"]


def test_r6_spending_against_a_zero_budget_is_fully_used():
    line = BudgetLine("Entertainment", limit=0, spent=500)
    assert line.percent_used == 100.0
    assert line.is_over is True
    assert BudgetLine("Entertainment", limit=0, spent=0).percent_used == 0.0
