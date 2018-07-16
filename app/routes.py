from flask import session, render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateForm, SelectForm, \
                      EditForm, CompleteForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Habit  # ,Completed
from werkzeug.urls import url_parse
from datetime import date


# populates a SelectMultipleField with habits of given day
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    all_habits = Habit.query.filter_by(user_id=current_user.id).all()
    days_habits = []
    today = date.today()
    for habit in all_habits:
        if habit.start_date <= today <= habit.end_date:
            days_habits.append(habit)
    form = CompleteForm()
    form.habits.choices = [(x.id, x.habit) for x in days_habits]
    if form.validate_on_submit():
        # what am I even submitting?
        thing = form.habits.data
        flash(thing)
        return redirect(url_for('create'))
    return render_template("index.html", title='Home Page', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateForm()
    if form.validate_on_submit():
        habit = Habit(habit=form.habit.data, start_date=form.start_date.data,
                      end_date=form.end_date.data, user_id=current_user.id)
        db.session.add(habit)
        db.session.commit()
        flash('New habit created')
        return redirect(url_for('index'))
    return render_template('create.html', title='Create Habit', form=form)


@app.route('/select', methods=['GET', 'POST'])
@login_required
def select():
    form = SelectForm()
    form.habit.choices = [(x.id, x.habit) for x in
                          Habit.query.filter_by(user_id=current_user.id)]
    if form.validate_on_submit():
        session['habit'] = form.habit.data
        return redirect(url_for('edit'))
    return render_template('select.html', title='Select Habit', form=form)
#
# the "session" started in "select" and used in "edit"
# could be a security hazard, the Flask documentation
# talks about how to encrypt this
#


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    x = session['habit']
    habit = Habit.query.filter_by(id=x).first()
    form = EditForm(habit=habit.habit, start_date=habit.start_date,
                    end_date=habit.end_date)
    if form.validate_on_submit():
        habit.habit = form.habit.data
        habit.start_date = form.start_date.data
        habit.end_date = form.end_date.data
        db.session.commit()
        flash('Habit edited')
        return redirect(url_for('index'))
    return render_template('edit.html', title='Edit Habit', form=form)
