from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
                    DateField, SelectField, SelectMultipleField, widgets
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
                               Optional
from app.models import User
from datetime import date


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


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
    select_date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SelectHabitForm(FlaskForm):
    habit = SelectField('Select Habit', coerce=int)
    submit = SubmitField('Edit Habit')


class CompleteForm(FlaskForm):
    habits = SelectMultipleField('Habits', coerce=int,
                                 widget=widgets.ListWidget(prefix_label=False),
                                 option_widget=widgets.CheckboxInput())
    submit = SubmitField('Submit')
