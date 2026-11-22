"""Reading and writing the local save file (R7).

This file is the only place that touches the disk. It knows nothing about the
rules beyond how to write a Ledger down and read one back, and nothing about
HTTP at all.

The file is plain JSON so you can open it in a text editor and see exactly what
the program is keeping. Amounts in it are whole cents, the same as in memory.
"""

import json
import os

from tracker import CATEGORIES, KINDS, Ledger, Transaction

DEFAULT_PATH = "data.json"
FORMAT_VERSION = 1


def to_dict(ledger):
    """The ledger as plain lists and dicts, ready for json.dump."""
    return {
        "version": FORMAT_VERSION,
        "transactions": [
            {
                "kind": transaction.kind,
                "amount": transaction.amount,
                "category": transaction.category,
                "description": transaction.description,
                "date": transaction.date,
            }
            for transaction in ledger.transactions
        ],
        "budgets": dict(ledger.budgets),
    }


def _transaction_from_row(row):
    """One saved row back into a Transaction, or ValueError saying what is wrong."""
    if not isinstance(row, dict):
        raise ValueError(f"a saved transaction is not a record: {row!r}")
    try:
        kind = row["kind"]
        amount = int(row["amount"])
        category = row["category"]
        date = row["date"]
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"a saved transaction is missing something: {row!r}") from None
    if kind not in KINDS:
        raise ValueError(f"a saved transaction has an unknown kind: {kind!r}")
    if category not in CATEGORIES:
        raise ValueError(f"a saved transaction has an unknown category: {category!r}")
    return Transaction(
        kind=kind,
        amount=amount,
        category=category,
        description=row.get("description", ""),
        date=date,
    )


def from_dict(data):
    """A saved file's contents back into a Ledger."""
    if not isinstance(data, dict):
        raise ValueError("the save file should hold a record, not a list or a number")
    transactions = [_transaction_from_row(row) for row in data.get("transactions", [])]
    budgets = {
        category: int(limit)
        for category, limit in (data.get("budgets") or {}).items()
        if category in CATEGORIES
    }
    return Ledger(transactions=transactions, budgets=budgets)


def save(ledger, path=DEFAULT_PATH):
    """Write the ledger to path. Returns the path written.

    It writes to a temporary file beside the real one and then renames it over
    the top. Renaming is a single step the operating system either does or does
    not do, so a crash halfway through cannot leave behind half a save file.
    """
    path = os.path.abspath(str(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(to_dict(ledger), handle, indent=2)
        handle.write("\n")
    os.replace(temporary, path)
    return path


def load(path=DEFAULT_PATH):
    """Read the ledger back. An empty Ledger when there is no file yet."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return Ledger()
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from None
    return from_dict(data)
