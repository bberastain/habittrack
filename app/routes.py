from flask import session, render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateForm, \
                      SelectHabitForm, EditForm, CompleteForm, \
                      SelectDateForm
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
        completed = Completed.query.filter_by(date
                        =ddate).filter(Completed.habit_id.in_(habit_ids)).all()
        selected = [i.habit_id for i in completed]
        hform.habits.data = selected

    # submit update to completed habits
    if hform.validate_on_submit() and hform.submit.data:
        habit_ids = [habit.id for habit in days_habits]
        completed = Completed.query.filter_by(date
                        =ddate).filter(Completed.habit_id.in_(habit_ids)).all()
        previous = [i.habit_id for i in completed]

        done = hform.habits.data  # checked boxes
        flash(done)
        # previous = session['done']
        new = []
        for id in done:
            if id not in previous:
                new.append(id)
            if id in previous:
                previous.remove(id)
        for id in new:
            checkbox = Completed(date=ddate, habit_id=id)
            db.session.add(checkbox)
            db.session.commit()
        for id in previous:
            checkbox = Completed.query.filter_by(date=ddate).filter_by(habit_id=id)
            db.session.delete(checkbox[0])
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
