from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Habit  # ,Completed
from werkzeug.urls import url_parse
from datetime import date


@app.route('/')
@app.route('/index')
@login_required
def index():
    habits = Habit.query.filter_by(user_id=current_user.id).all()

    def is_between(start_date, end_date, today):

        #
        # save as utc seconds and compare those instead!!!
        # Only the view function needs to see it in calendar form
        #
        return True

    days_habits = []
    today = date.today()
    for habit in habits:
        if is_between(habit.start_date, today, habit.end_date):
            days_habits.append(habit.habit)
    return render_template("index.html", title='Home Page', habits=days_habits)

# user = User.query.filter_by(username=current_user).first()
# habits = Habit.query.filter_by(current_user.habit)
# fits in a "for habit in habits" block in the 'index' template
# find out the logic they use for "posts", equivalent of "habits"
# I guess it'd be a form that gets submitted


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
