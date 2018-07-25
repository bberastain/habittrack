from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, \
                    SelectMultipleField, widgets
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Optional
from datetime import date


class CreateForm(FlaskForm):
    habit = StringField('Habit', validators=[DataRequired('something')])
    # how do I make "description" visibile to users?
    start_date = DateField('Start Date', default=date.today,
                           validators=[Optional()], description="Optional, \
                           defaults to today's date")
    end_date = DateField('End Date', default=date(9999, 1, 1),
                         validators=[Optional()], description='Optional, \
                         defaults to 9999-01-01')
    submit = SubmitField('Submit')


class EditForm(FlaskForm):  # Could I just inherit CreateForm?
    habit = StringField('Habit', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    submit = SubmitField('Submit')


class SelectDateForm(FlaskForm):
    select_date = DateField('DatePicker', format='%Y-%m-%d')
    submit = SubmitField('Select Date')


class SelectHabitForm(FlaskForm):
    habit = SelectField('Select Habit', coerce=int)
    submit = SubmitField('Edit Habit')


class CompleteForm(FlaskForm):
    habits = SelectMultipleField('Habits', coerce=int,
                                 widget=widgets.TableWidget(),
                                 option_widget=widgets.CheckboxInput())
    submit = SubmitField('Submit Completed Habits')


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[Optional()])
    date = DateField('Date Finished', default=date.today)
    submit = SubmitField('Submit Finished Book')
