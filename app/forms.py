from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField,SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange
from .models import User

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    nickname = StringField('Nickname', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered.')

    def validate_nickname(self, nickname):
        user = User.query.filter_by(nickname=nickname.data).first()
        if user is not None:
            raise ValidationError('Nickname already in use.')

class LoginForm(FlaskForm):
    login = StringField('Email or Nickname', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class JokeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    body = TextAreaField('Joke', validators=[DataRequired()])
    submit = SubmitField('Submit Joke')
    def validate_title(self, title):
        # Validate that the title has no more than 10 words
        if len(title.data.split()) > 10:
            raise ValidationError('The title must not exceed 10 words.')
class RatingForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Rating')
class UpdateJokeForm(FlaskForm):
    body = TextAreaField('Joke Body', validators=[DataRequired()])
    submit = SubmitField('Update Joke')

class EditBalanceForm(FlaskForm):
    user_id = SelectField('User', coerce=int)  # Dropdown populated with users
    new_balance = IntegerField('New Balance', validators=[DataRequired()])
    submit = SubmitField('Update Balance')