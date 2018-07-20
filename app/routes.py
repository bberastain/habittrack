from flask import session, render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateForm, \
                      SelectHabitForm, EditForm, CompleteForm, \
                      SelectDateForm, ResetPasswordRequestForm, \
                      ResetPasswordForm
from app.email import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Habit, Completed
from werkzeug.urls import url_parse
from datetime import date


# the "sessions" started could be a security hazard,
# the Flask documentation talks about how to encrypt it


def date_from_string(day):
    # accepts '%Y-%m-%d'
    temp = day.split('-')
    year, month, day = int(temp[0]), int(temp[1]), int(temp[2])
    day = date(year, month, day)
    return day


def habits_given_date(day):
    # accepts datetime.date or string
    if type(day) == str:
        day = date_from_string(day)
    all_habits = Habit.query.filter_by(user_id=current_user.id).all()
    days_habits = []
    for habit in all_habits:
        if habit.start_date <= day <= habit.end_date:
            days_habits.append(habit)
    return days_habits


# still need to prepopulate with completed habits,
# check them against submitted data, and edit database accordingly
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    # initial datetime.date
    if session.get('today'):
        dstring = session['today']
        ddate = date_from_string(dstring)
    else:
        ddate = date.today()

    # display habits
    days_habits = habits_given_date(ddate)
    hform = CompleteForm(prefix='hform')  # habits form
    hform.habits.choices = [(x.id, x.habit) for x in days_habits]

    # prepopulate habits
    if request.method == 'GET':
        habit_ids = [habit.id for habit in days_habits]
        completed = Completed.query.filter_by(
            date=ddate).filter(Completed.habit_id.in_(habit_ids)).all()
        selected = [i.habit_id for i in completed]
        hform.habits.data = selected
        session['done'] = selected

    # submit update to completed habits
    if hform.validate_on_submit() and hform.submit.data:
        previous = session['done']
        done = hform.habits.data  # checked boxes
        for id in done:
            if id in previous:
                done.remove(id)
                previous.remove(id)
        for id in done:
            x = Completed(date=ddate, habit_id=id)
            db.session.add(x)
            db.session.commit()
        for id in previous:
            x = Completed.query.filter_by(date=ddate).filter_by(habit_id=id)
            db.session.delete(x[0])
            db.session.commit()
        flash('Completed Habits Updated')
        return redirect(url_for('index'))

    # submit selected date
    sdform = SelectDateForm(prefix='sdform')  # select-date form
    if sdform.validate_on_submit() and sdform.submit.data:
        session['today'] = sdform.select_date.data.strftime('%Y-%m-%d')
        return redirect(url_for('index'))

    return render_template('index.html', hform=hform, sdform=sdform,
                           d1=date.today(), d2=ddate, days_habits=days_habits)


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


@app.route('/select_habit', methods=['GET', 'POST'])
@login_required
def select_habit():
    form = SelectHabitForm()
    form.habit.choices = [(x.id, x.habit) for x in
                          Habit.query.filter_by(user_id=current_user.id)]
    if form.validate_on_submit():
        session['habit'] = form.habit.data
        return redirect(url_for('edit'))
    return render_template('select_habit.html', title='Select Habit',
                           form=form)


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


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/stats', methods=['GET'])
@login_required
def stats():
    # for each habit display totals as a fraction and percentage
    today = date.today()
    all_habits = Habit.query.filter_by(user_id=current_user.id).filter_by.all()
    for habit in all_habits:
        pass
        # use 'datetime' module to find the difference in days here
        # total = today - habit.start_date (find "length" as an integer)

        # done = Completed.query.filter_by(habit_id=habit.id)
        # further filter by completed.date <= habit.end_date
        # then find the length of the list returned

        # use 'decimal' module here to round to one or two places
        # percentage = done/total

    return render_template('stats.html', title='Habit Stats')
