from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///excavator.db'
db = SQLAlchemy(app)

# Database Models
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'Income' or 'Expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200))
    partner = db.Column(db.String(20), nullable=False, default='All')

# Partner Contributions
partner_contributions = {
    'Hamayo': 85000,   # Partner A
    'Waqar': 43000,    # Partner B
    'Omer': 152000     # Partner C
}
total_investment = sum(partner_contributions.values())

# Authentication Info
USERNAME = 'omer'
PASSWORD = 'Omer6219'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('dashboard.html', transactions=transactions)

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        transaction = Transaction(
            date=date,
            type=request.form['type'],
            category=request.form['category'],
            amount=float(request.form['amount']),
            note=request.form.get('note'),
            partner=request.form['partner']
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add.html', partners=list(partner_contributions.keys()) + ['All'])

@app.route('/report')
def report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    transactions = Transaction.query.all()
    summary = {}
    for t in transactions:
        month = t.date.strftime('%Y-%m')
        if month not in summary:
            summary[month] = {'Income': 0, 'Expense': 0}
        summary[month][t.type] += t.amount
    for month in summary:
        profit = summary[month]['Income'] - summary[month]['Expense']
        summary[month]['Profit'] = profit
        summary[month]['Shares'] = {
            p: round(profit * c / total_investment, 2) for p, c in partner_contributions.items()
        }
    total_income = sum(t.amount for t in transactions if t.type == 'Income')
    total_expense = sum(t.amount for t in transactions if t.type == 'Expense')
    total_profit = total_income - total_expense
    total_shares = {
        p: round(total_profit * c / total_investment, 2) for p, c in partner_contributions.items()
    }
    return render_template('report.html', summary=summary, total_profit=total_profit, total_shares=total_shares)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
