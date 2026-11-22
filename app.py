"""The web front end.

This file holds no rules. It reads the form, hands the values to tracker.py,
saves through storage.py, and renders the page. That is why there are no tests
for it: everything worth testing lives in the other two files.

Run it with:

    python3 app.py

then open http://127.0.0.1:5000 in a browser.
"""

import os

from flask import Flask, redirect, render_template, request, url_for

import storage
from tracker import CATEGORIES, EXPENSE, INCOME, format_amount, today

# Where the save file lives. Overridable so you can try the app out without
# touching your own data.json.
DATA_PATH = os.environ.get("FINANCE_TRACKER_DATA", storage.DEFAULT_PATH)

app = Flask(__name__)
app.jinja_env.filters["money"] = format_amount


def current_month():
    """The month the page is showing: whatever was asked for, else this one."""
    return request.values.get("month") or today()[:7]


def page(error=None, status=200):
    """Render the one page from whatever is currently saved."""
    ledger = storage.load(DATA_PATH)
    month = current_month()
    return (
        render_template(
            "index.html",
            categories=CATEGORIES,
            income_kind=INCOME,
            expense_kind=EXPENSE,
            month=month,
            today=today(),
            transactions=ledger.in_order(),
            total_income=ledger.total_income(month),
            total_expenses=ledger.total_expenses(month),
            balance=ledger.balance(month),
            all_time_balance=ledger.balance(),
            budget_lines=ledger.budget_report(month),
            error=error,
        ),
        status,
    )


@app.get("/")
def index():
    return page()


@app.post("/transactions")
def add_transaction():
    """R1, R2. Record one income or expense."""
    ledger = storage.load(DATA_PATH)
    try:
        ledger.record(
            request.form.get("kind", ""),
            request.form.get("amount", ""),
            request.form.get("category", ""),
            request.form.get("description", ""),
            request.form.get("date", ""),
        )
    except ValueError as error:
        # Re-show the page with the message rather than losing what was typed.
        return page(error=str(error), status=400)
    storage.save(ledger, DATA_PATH)
    return redirect(url_for("index", month=current_month()))


@app.post("/budgets")
def set_budget():
    """R5. Set the monthly limit for one category."""
    ledger = storage.load(DATA_PATH)
    try:
        ledger.set_budget(request.form.get("category", ""), request.form.get("amount", ""))
    except ValueError as error:
        return page(error=str(error), status=400)
    storage.save(ledger, DATA_PATH)
    return redirect(url_for("index", month=current_month()))


if __name__ == "__main__":
    # 127.0.0.1 means this machine only: nothing on the network can reach it.
    app.run(host="127.0.0.1", port=5000)
