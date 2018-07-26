from flask import session, render_template, flash, redirect, url_for, request
from app import db
from app.main.forms import CreateForm, SelectHabitForm, EditForm, \
    CompleteForm, SelectDateForm
from flask_login import current_user, login_required
from app.models import Habit, Completed
from datetime import date
from app.main import bp
from decimal import Decimal, getcontext


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
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))

    # submit selected date
    sdform = SelectDateForm(prefix='sdform')  # select-date form
    if sdform.validate_on_submit() and sdform.submit.data:
        session['today'] = sdform.select_date.data.strftime('%Y-%m-%d')
        return redirect(url_for('main.index'))

    goals = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', hform=hform, sdform=sdform,
                           d1=date.today(), d2=ddate, days_habits=days_habits,
                           goals=goals)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateForm()
    if form.validate_on_submit():
        habit = Habit(habit=form.habit.data, start_date=form.start_date.data,
                      end_date=form.end_date.data, user_id=current_user.id)
        db.session.add(habit)
        db.session.commit()
        flash('New habit created')
        return redirect(url_for('main.index'))
    return render_template('create.html', title='Create Habit', form=form)


@bp.route('/select_habit', methods=['GET', 'POST'])
@login_required
def select_habit():
    form = SelectHabitForm()
    form.habit.choices = [(x.id, x.habit) for x in
                          Habit.query.filter_by(user_id=current_user.id)]
    if form.validate_on_submit():
        session['habit'] = form.habit.data
        return redirect(url_for('main.edit'))
    return render_template('select_habit.html', title='Select Habit',
                           form=form)


@bp.route('/edit', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))
    return render_template('edit.html', title='Edit Habit', form=form)


@bp.route('/stats', methods=['GET'])
@login_required
def stats():
    # for each habit display totals as a fraction and percentage
    today = date.today()
    all_habits = Habit.query.filter_by(user_id=current_user.id).all()
    hlist, tlist, clist, plist = [], [], [], []
    for habit in all_habits:
        hlist.append(habit.habit)
        difference = today - habit.start_date
        total = difference.days + 1  # add one for fence-post problem
        tlist.append(total)
        completed = Completed.query.filter_by(habit_id=habit.id).all()
        counter = 0
        for instance in completed:
            if instance.date <= today:
                counter += 1
        clist.append(counter)
        getcontext().prec = 2
        percent = int(Decimal(counter) / Decimal(total) * 100)
        plist.append(percent)
    stats = list(zip(hlist, tlist, clist, plist))
    return render_template('stats.html', title='Habit Stats', stats=stats)
