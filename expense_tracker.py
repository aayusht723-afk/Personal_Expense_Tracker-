from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
from pathlib import Path
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "replace-with-your-own-secret-key"
DB_PATH = Path(__file__).with_name("expenses.db")

CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills",
    "Education", "Health", "Entertainment", "Other"
]

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Personal Expense Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box}
:root{font-family:Arial,Helvetica,sans-serif;color:#182230;background:#f5f7fb}
body{margin:0;background:#f5f7fb}
.topbar{background:#fff;border-bottom:1px solid #e6eaf0;padding:16px 5%;display:flex;justify-content:space-between;align-items:center;gap:15px}
.brand{display:flex;align-items:center;gap:12px}
.logo{width:43px;height:43px;border-radius:12px;background:#e8f7ef;color:#168653;display:grid;place-items:center;font-size:25px;font-weight:bold}
.brand h2{font-size:17px;margin:0 0 4px}.brand small{color:#7b8794}
.container{width:min(1180px,92%);margin:30px auto}
.intro{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:22px}
.eyebrow{color:#168653;letter-spacing:1.5px;font-size:11px;font-weight:bold}
h1{font-size:clamp(27px,4vw,36px);margin:8px 0}
.muted{color:#7b8794;font-size:13px;line-height:1.5}
.month-filter{display:flex;gap:8px;align-items:end;flex-wrap:wrap}
.month-filter label{width:100%}
input,select{width:100%;min-width:0;padding:11px;border:1px solid #d9e0e8;border-radius:9px;background:white;font:inherit;font-size:13px}
.month-filter input{width:155px}
label{display:block;font-size:12px;font-weight:bold;color:#475467;margin:8px 0 6px}
button{border:0;border-radius:9px;padding:11px 15px;font-size:13px;font-weight:bold;cursor:pointer}
.primary{background:#168653;color:white}.secondary{background:white;border:1px solid #d9e0e8;color:#344054}
.full{width:100%;margin-top:12px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.stat,.panel{background:#fff;border:1px solid #e8ecf2;border-radius:15px;box-shadow:0 4px 16px #1d293908}
.stat{padding:20px}
.stat-label{font-size:13px;color:#667085}.stat-value{font-size:28px;font-weight:bold;margin:10px 0 5px}.stat-note{font-size:12px;color:#98a2b3}
.main-grid{display:grid;grid-template-columns:.95fr 1.05fr;gap:18px}
.panel{padding:22px;min-width:0}
.panel-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;gap:10px}
.panel h2{font-size:17px;margin:0 0 5px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
form.expense-form{display:grid;gap:4px}
.chart-wrap{height:245px;position:relative}
.monthly{grid-column:1/-1}.monthly .chart-wrap{height:260px}
.history{margin-top:20px}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px;text-align:left}
th,td{padding:14px 11px;border-bottom:1px solid #edf0f4;white-space:nowrap}
th{font-size:11px;color:#7b8794;background:#fafbfc;text-transform:uppercase}
.number{text-align:right}.amount{font-weight:bold}
.pill{display:inline-block;background:#f0f3f7;border-radius:20px;padding:6px 10px;font-size:11px;color:#475467}
.delete{background:#fff0ee;color:#b42318;border:1px solid #f2c9c5;padding:7px 10px}
.notice{padding:12px 14px;border-radius:9px;margin-bottom:15px;font-size:13px}
.success{background:#e8f7ef;color:#11683f}.error{background:#fff0ee;color:#b42318}
.empty{text-align:center;padding:28px;color:#7b8794;font-size:13px}
footer{text-align:center;padding:25px 0;color:#98a2b3;font-size:12px}
@media(max-width:760px){
 .topbar{padding:14px 4%}.today{display:none}.container{margin-top:22px}
 .intro{align-items:flex-start;flex-direction:column}.stats{grid-template-columns:1fr}
 .main-grid{grid-template-columns:1fr}.monthly{grid-column:auto}
 .form-row{grid-template-columns:1fr}.panel{padding:17px}
}
</style>
</head>
<body>
<header class="topbar">
  <div class="brand"><div class="logo">₹</div><div><h2>Expense Tracker</h2><small>Personal finance dashboard</small></div></div>
  <div class="today muted">Today: {{ today }}</div>
</header>
<main class="container">
  <section class="intro">
    <div><div class="eyebrow">YOUR MONEY, MADE CLEAR</div><h1>Expense Dashboard</h1><div class="muted">Record spending, track categories, and understand your monthly habits.</div></div>
    <form method="get" class="month-filter">
      <label for="month">Chart month</label><input id="month" type="month" name="month" value="{{ selected_month }}">
      <button class="secondary" type="submit">Apply</button>
    </form>
  </section>

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for kind, message in messages %}<div class="notice {{ kind }}">{{ message }}</div>{% endfor %}
  {% endwith %}

  <section class="stats">
    <article class="stat"><div class="stat-label">All-time expenses</div><div class="stat-value">₹{{ "%.2f"|format(total_expenses) }}</div><div class="stat-note">Total recorded spending</div></article>
    <article class="stat"><div class="stat-label">Selected month</div><div class="stat-value">₹{{ "%.2f"|format(month_expenses) }}</div><div class="stat-note">{{ selected_month }} spending</div></article>
    <article class="stat"><div class="stat-label">Transactions</div><div class="stat-value">{{ expenses|length }}</div><div class="stat-note">All recorded expenses</div></article>
  </section>

  <section class="main-grid">
    <article class="panel">
      <div class="panel-head"><div><h2>Add an expense</h2><div class="muted">Enter expense details below.</div></div><div class="logo">＋</div></div>
      <form action="{{ url_for('add_expense') }}" method="post" class="expense-form">
        <label for="title">Expense title</label><input id="title" name="title" maxlength="100" placeholder="e.g. Lunch, Bus fare" required>
        <div class="form-row">
          <div><label for="amount">Amount (₹)</label><input id="amount" name="amount" type="number" min="0.01" step="0.01" placeholder="250.00" required></div>
          <div><label for="category">Category</label><select id="category" name="category">{% for c in categories %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select></div>
        </div>
        <label for="expense_date">Date</label><input id="expense_date" name="expense_date" type="date" value="{{ today }}" required>
        <button class="primary full" type="submit">＋ Add expense</button>
      </form>
    </article>

    <article class="panel">
      <div class="panel-head"><div><h2>Spending by category</h2><div class="muted">For {{ selected_month }}</div></div></div>
      <div class="chart-wrap"><canvas id="categoryChart"></canvas></div>
      {% if not category_labels %}<div class="empty">Add expenses for this month to see the chart.</div>{% endif %}
    </article>

    <article class="panel monthly">
      <div class="panel-head"><div><h2>Monthly spending</h2><div class="muted">Your latest recorded months</div></div></div>
      <div class="chart-wrap"><canvas id="monthlyChart"></canvas></div>
      {% if not month_labels %}<div class="empty">Your monthly chart will appear after you add expenses.</div>{% endif %}
    </article>
  </section>

  <section class="panel history">
    <div class="panel-head"><div><h2>Transaction history</h2><div class="muted">All recorded expenses</div></div><span class="pill">{{ expenses|length }} records</span></div>
    {% if expenses %}
    <div class="table-wrap"><table>
      <thead><tr><th>Date</th><th>Title</th><th>Category</th><th class="number">Amount</th><th>Action</th></tr></thead>
      <tbody>{% for e in expenses %}
        <tr>
          <td>{{ e["expense_date"] }}</td><td><strong>{{ e["title"] }}</strong></td>
          <td><span class="pill">{{ e["category"] }}</span></td>
          <td class="number amount">₹{{ "%.2f"|format(e["amount"]) }}</td>
          <td><form action="{{ url_for('delete_expense', expense_id=e['id']) }}" method="post" onsubmit="return confirm('Delete this expense?')"><button class="delete" type="submit">Delete</button></form></td>
        </tr>
      {% endfor %}</tbody>
    </table></div>
    {% else %}<div class="empty">No expenses yet. Add your first expense using the form above.</div>{% endif %}
  </section>
  <footer>Personal Expense Tracker · AIP Mini Project · Python, Flask and SQLite</footer>
</main>
<script>
const categoryLabels = {{ category_labels|tojson }};
const categoryValues = {{ category_values|tojson }};
const monthLabels = {{ month_labels|tojson }};
const monthValues = {{ month_values|tojson }};
new Chart(document.getElementById("categoryChart"), {
  type:"doughnut",
  data:{labels:categoryLabels,datasets:[{data:categoryValues,borderWidth:2}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}}}
});
new Chart(document.getElementById("monthlyChart"), {
  type:"bar",
  data:{labels:monthLabels,datasets:[{label:"Spending (₹)",data:monthValues,borderWidth:1}]},
  options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,title:{display:true,text:"Amount (₹)"}}},plugins:{legend:{display:false}}}
});
</script>
</body>
</html>
"""


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)


@app.route("/")
def index():
    today = date.today()
    selected_month = request.args.get("month", today.strftime("%Y-%m"))
    try:
        datetime.strptime(selected_month, "%Y-%m")
    except ValueError:
        selected_month = today.strftime("%Y-%m")

    with connect_db() as connection:
        expenses = connection.execute(
            "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC"
        ).fetchall()
        total = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
        ).fetchone()["total"]
        month_total = connection.execute(
            """SELECT COALESCE(SUM(amount), 0) AS total FROM expenses
               WHERE substr(expense_date, 1, 7) = ?""",
            (selected_month,)
        ).fetchone()["total"]
        category_rows = connection.execute(
            """SELECT category, SUM(amount) AS total FROM expenses
               WHERE substr(expense_date, 1, 7) = ?
               GROUP BY category ORDER BY total DESC""",
            (selected_month,)
        ).fetchall()
        monthly_rows = connection.execute(
            """SELECT substr(expense_date, 1, 7) AS month, SUM(amount) AS total
               FROM expenses GROUP BY substr(expense_date, 1, 7)
               ORDER BY month DESC LIMIT 6"""
        ).fetchall()

    monthly_rows = list(reversed(monthly_rows))
    return render_template_string(
        HTML,
        today=today.isoformat(),
        selected_month=selected_month,
        expenses=expenses,
        categories=CATEGORIES,
        total_expenses=round(total, 2),
        month_expenses=round(month_total, 2),
        category_labels=[r["category"] for r in category_rows],
        category_values=[round(r["total"], 2) for r in category_rows],
        month_labels=[r["month"] for r in monthly_rows],
        month_values=[round(r["total"], 2) for r in monthly_rows]
    )


@app.route("/add", methods=["POST"])
def add_expense():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Other").strip()
    amount_text = request.form.get("amount", "").strip()
    expense_date = request.form.get("expense_date", "").strip()

    try:
        amount = float(amount_text)
    except (TypeError, ValueError):
        amount = 0

    try:
        datetime.strptime(expense_date, "%Y-%m-%d")
        valid_date = True
    except ValueError:
        valid_date = False

    if not title:
        flash("Please enter an expense title.", "error")
    elif amount <= 0:
        flash("Amount must be greater than zero.", "error")
    elif category not in CATEGORIES:
        flash("Please choose a valid category.", "error")
    elif not valid_date:
        flash("Please choose a valid date.", "error")
    else:
        with connect_db() as connection:
            connection.execute(
                """INSERT INTO expenses (title, amount, category, expense_date)
                   VALUES (?, ?, ?, ?)""",
                (title, amount, category, expense_date)
            )
        flash("Expense added successfully.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    with connect_db() as connection:
        connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    flash("Expense deleted successfully.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    print("Personal Expense Tracker is running.")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)
