from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Length, EqualTo, Email


class RegisterForm(FlaskForm):
    """ Form for registering a user """

    username = StringField(
        "Username", validators=[InputRequired(),
                                Length(min=3, max=20)])
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            EqualTo('confirm', message='Passwords must match')
        ])
    confirm = PasswordField("Confirm Password")

    email = EmailField("Email", validators=[InputRequired(), Email()])

    first_name = StringField(
        "First Name", validators=[InputRequired(),
                                  Length(min=1, max=30)])

    last_name = StringField(
        "Last Name", validators=[InputRequired(),
                                 Length(min=1, max=30)])


class LoginForm(FlaskForm):
    """ Form for logging in a user """

    username = StringField(
        "Username", validators=[InputRequired(),
                                Length(min=3, max=20)])
    password = PasswordField("Password", validators=[InputRequired()])


class AddFeedbackForm(FlaskForm):
    """ add a feedback under the user who is authenticated """

    title = StringField("Title", validators=[InputRequired(), Length(max=100)])
    content = StringField("Content", validators=[InputRequired()])


class UpdateFeedbackForm(FlaskForm):
    """ update a feedback under the user who is authenticated """

    title = StringField("Title", validators=[InputRequired(), Length(max=100)])
    content = StringField("Content", validators=[InputRequired()])
