from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.sqlite3'
app.config['SECRET_KEY'] = 'secret_key123'

db = SQLAlchemy(app)



class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank = db.Column(db.String(50), nullable=False)

    expenses = db.relationship('Expenses', backref='bank', lazy=True)
    salaries = db.relationship('Salaries', backref='bank', lazy=True)


EXPENSE_CATEGORIES = [
    'Food & Dining',
    'Transport',
    'Shopping',
    'Utilities',
    'Health',
    'Entertainment',
    'Education',
    'Rent',
    'Other',
]

class Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_name = db.Column(db.String(100))
    expense_amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)


class Salaries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)




@app.route('/')
def home():
    return render_template("index.html")



@app.route('/select_bank', methods=['GET', 'POST'])
def select_bank():
    banks = Bank.query.all()

    if request.method == 'POST':
        bank_id = int(request.form['bank_id'])
        session['bank_id'] = bank_id
        return redirect(url_for('dashboard'))

    return render_template("select_bank.html", banks=banks)



@app.route('/dashboard')
def dashboard():
    bank_id = session.get('bank_id')

    if not bank_id:
        return redirect(url_for('select_bank'))

    expenses = Expenses.query.filter_by(bank_id=bank_id).all()
    salaries = Salaries.query.filter_by(bank_id=bank_id).all()

    total_expenses = sum(e.expense_amount for e in expenses)
    total_salary = sum(s.amount for s in salaries)

    balance = total_salary - total_expenses

    return render_template(
        "dashboard.html",
        balance=balance,
        total_expenses=total_expenses,
        total_salary=total_salary
    )



@app.route('/expenses')
def expenses():
    return render_template("expenses.html")


@app.route('/expenses/add', methods=['GET', 'POST'])
def add_expenses():
    if request.method == 'POST':
        name = request.form['expense_name']
        amount = float(request.form['expense_amount'])
        category = request.form['category']

        bank_id = session.get('bank_id')
        if not bank_id:
            return redirect(url_for('select_bank'))

        total_salary = sum(s.amount for s in Salaries.query.filter_by(bank_id=bank_id).all())
        total_expenses = sum(e.expense_amount for e in Expenses.query.filter_by(bank_id=bank_id).all())

        if total_expenses + amount > total_salary:
            error = f"Cannot add expense. It would exceed your available balance of ₹{total_salary - total_expenses:.2f}."
            return render_template("add_expense.html", error=error, categories=EXPENSE_CATEGORIES)

        expense = Expenses(
            expense_name=name,
            expense_amount=amount,
            category=category,
            bank_id=bank_id
        )

        db.session.add(expense)
        db.session.commit()

        return redirect(url_for('view_expenses'))

    return render_template("add_expense.html", categories=EXPENSE_CATEGORIES)


@app.route('/expenses/view')
def view_expenses():
    bank_id = session.get('bank_id')

    if not bank_id:
        return redirect(url_for('select_bank'))

    expenses = Expenses.query.filter_by(bank_id=bank_id).all()

    return render_template("view_expenses.html", expenses=expenses)



@app.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    expense = Expenses.query.get_or_404(id)

    if request.method == 'POST':
        expense.expense_name = request.form['expense_name']
        expense.expense_amount = request.form['expense_amount']
        expense.category = request.form['category']

        db.session.commit()
        return redirect(url_for('view_expenses'))

    return render_template("edit_expense.html", expense=expense, categories=EXPENSE_CATEGORIES)



@app.route('/expenses/delete/<int:id>')
def delete_expense(id):
    expense = Expenses.query.get_or_404(id)

    db.session.delete(expense)
    db.session.commit()

    return redirect(url_for('view_expenses'))



@app.route('/salaries')
def salaries():
    return render_template("salaries.html")


@app.route('/salaries/add', methods=['GET', 'POST'])
def add_salary():
    if request.method == 'POST':
        month = request.form['month']
        amount = request.form['salary_amount']

        bank_id = session.get('bank_id')
        if not bank_id:
            return redirect(url_for('select_bank'))

        salary = Salaries(
            month=month,
            amount=amount,
            bank_id=bank_id
        )

        db.session.add(salary)
        db.session.commit()

        return redirect(url_for('view_salary'))

    return render_template("add_salary.html")


@app.route('/salaries/view')
def view_salary():
    bank_id = session.get('bank_id')

    if not bank_id:
        return redirect(url_for('select_bank'))

    salaries = Salaries.query.filter_by(bank_id=bank_id).all()

    return render_template("view_salaries.html", salaries=salaries)




@app.route('/salaries/edit/<int:id>', methods=['GET', 'POST'])
def edit_salary(id):
    salary = Salaries.query.get_or_404(id)

    if request.method == 'POST':
        salary.month = request.form['month']
        salary.amount = request.form['salary_amount']

        db.session.commit()
        return redirect(url_for('view_salary'))

    return render_template("edit_salary.html", salary=salary)


@app.route('/salaries/delete/<int:id>')
def delete_salary(id):
    salary = Salaries.query.get_or_404(id)

    db.session.delete(salary)
    db.session.commit()

    return redirect(url_for('view_salary'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if Bank.query.count() == 0:
            db.session.add(Bank(bank="SBI"))
            db.session.add(Bank(bank="Canara"))
            db.session.add(Bank(bank="Union"))
            db.session.commit()

    app.run(debug=True)