from flask import Flask, render_template, redirect, session
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized
from models import connect_db, db, User
from forms import RegisterForm, LoginForm
from secret import FLASK_SECRET_KEY, POSTGRESQL_DB

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRESQL_DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route('/')
def send_to_register():
    """ redirect main page to /register """

    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def user_registration():
    """ displays registration form """

    form = RegisterForm()

    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email, first_name, last_name)

        # code for optimization
        # # create copy of form dict
        # user_form_attr = dict(form.data)

        # # remove csrf_token from pet attributes
        # del user_form_attr['csrf_token']
        # del user_form_attr['confirm']

        # # unpack dict properties as keyword arguments for Pet Creation
        # user = User.register(**user_form_attr)

        try:
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            # in case username is already registered
            form.username.errors = [
                "Your username choice is lacking. Choose another!!!!"]
            return render_template("register.html", form=form)

        session["username"] = user.username

        # this is the resource we want to send someone after registering
        return redirect("/secret")

    else:
        return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    """ handle user login """

    form = LoginForm()

    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            session["username"] = user.username
            return redirect('/secret')

        else:
            # we got back false, send back to login form with error

            form.username.errors = [
                'You may have mistyped, type in the correct stuff!!!']
            return render_template("login.html", form=form)

    else:
        return render_template("login.html", form=form)
