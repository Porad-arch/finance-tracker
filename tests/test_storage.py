"""Tests for the save file.

R7. Save financial information locally so it is available when the application
is reopened.

`tmp_path` is a fresh empty directory pytest hands each test, so these never
touch a real data.json.
"""

import json

import pytest

import storage
from tracker import EXPENSE, INCOME, Ledger


def sample_ledger():
    ledger = Ledger()
    ledger.record(INCOME, "2500.00", "Other", "paycheck", "2026-11-01")
    ledger.record(EXPENSE, "45.50", "Food", "groceries", "2026-11-03")
    ledger.set_budget("Food", "400.00")
    ledger.set_budget("Housing", "1200.00")
    return ledger


def test_r7_loading_a_file_that_is_not_there_gives_an_empty_ledger(tmp_path):
    ledger = storage.load(tmp_path / "nothing-here.json")
    assert ledger.transactions == []
    assert ledger.budgets == {}


def test_r7_saving_then_loading_gives_back_the_same_transactions(tmp_path):
    path = tmp_path / "data.json"
    original = sample_ledger()
    storage.save(original, path)
    reloaded = storage.load(path)
    assert reloaded.transactions == original.transactions


def test_r7_budgets_survive_the_round_trip(tmp_path):
    path = tmp_path / "data.json"
    storage.save(sample_ledger(), path)
    assert storage.load(path).budgets == {"Food": 40000, "Housing": 120000}


def test_r7_the_totals_are_the_same_after_reopening(tmp_path):
    path = tmp_path / "data.json"
    storage.save(sample_ledger(), path)
    reloaded = storage.load(path)
    assert reloaded.total_income() == 250000
    assert reloaded.total_expenses() == 4550
    assert reloaded.balance() == 245450


def test_r7_amounts_come_back_as_whole_cents_not_floats(tmp_path):
    path = tmp_path / "data.json"
    storage.save(sample_ledger(), path)
    for transaction in storage.load(path).transactions:
        assert isinstance(transaction.amount, int)
    assert storage.load(path).transactions[1].amount == 4550


def test_r7_the_budget_report_is_the_same_after_reopening(tmp_path):
    path = tmp_path / "data.json"
    before = sample_ledger().budget_report("2026-11")
    storage.save(sample_ledger(), path)
    assert storage.load(path).budget_report("2026-11") == before


def test_r7_a_new_transaction_is_there_after_saving_again(tmp_path):
    path = tmp_path / "data.json"
    storage.save(sample_ledger(), path)
    ledger = storage.load(path)
    ledger.record(EXPENSE, "12.00", "Transport", "bus pass", "2026-11-04")
    storage.save(ledger, path)
    assert len(storage.load(path).transactions) == 3


def test_r7_the_save_file_is_plain_readable_json(tmp_path):
    path = tmp_path / "data.json"
    storage.save(sample_ledger(), path)
    data = json.loads(path.read_text())
    assert data["version"] == storage.FORMAT_VERSION
    assert data["budgets"]["Food"] == 40000
    assert data["transactions"][0]["amount"] == 250000


def test_r7_saving_leaves_no_temporary_file_behind(tmp_path):
    storage.save(sample_ledger(), tmp_path / "data.json")
    storage.save(sample_ledger(), tmp_path / "data.json")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["data.json"]


def test_r7_refuses_a_saved_transaction_with_an_unknown_category(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "transactions": [
                    {
                        "kind": "expense",
                        "amount": 100,
                        "category": "Yachts",
                        "date": "2026-11-01",
                    }
                ],
                "budgets": {},
            }
        )
    )
    with pytest.raises(ValueError):
        storage.load(path)


def test_r7_refuses_a_file_that_is_not_json(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("this is not json at all")
    with pytest.raises(ValueError):
        storage.load(path)
