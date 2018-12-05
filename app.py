from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, AddFeedbackForm, UpdateFeedbackForm
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
                "Your username choice is lacking. Choose another!!!!"
            ]
            return render_template("register.html", form=form)

        session["username"] = user.username
        flash(f'{username} has registed')

        # this is the resource we want to send someone after registering
        return redirect(f"/users/{username}")

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
            flash(f'{username} have logged in')
            return redirect(f'/users/{username}')

        else:
            # we got back false, send back to login form with error

            form.username.errors = [
                'You may have mistyped, type in the correct stuff!!!'
            ]
            return render_template("login.html", form=form)

    else:
        return render_template("login.html", form=form)


@app.route('/users/<username>')
def display_user_detail(username):
    """ display the user details excepts pw """

    if not session["username"] == username:
        raise Unauthorized()

    else:
        user = User.query.filter_by(username=username).first()
        feedbacks = user.feedbacks

        return render_template(
            'user_details.html', user=user, feedbacks=feedbacks)


@app.route('/logout')
def logout():
    """ log out the user and clean the session, redirect to main"""

    session.clear()
    return redirect('/')


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """ delete the user """

    if not session["username"] == username:
        raise Unauthorized()

    else:
        user = User.query.filter_by(username=username).first()
        db.session.delete(user)
        db.session.commit()

        return redirect('/')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """ add feedbacks """

    if not session["username"] == username:
        raise Unauthorized()
    else:
        # we add a feedback for this user

        form = AddFeedbackForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            new_feedback = Feedback.create_feedback(title, content, username)
            db.session.add(new_feedback)
            db.session.commit()
            flash('You added one feedback!')
            return redirect(f'/users/{username}')

        else:
            return render_template(
                "add_feedback.html", form=form, username=username)


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id: int):
    """ update feedbacks """

    current_feedback = Feedback.query.filter_by(id=feedback_id).first()
    username = current_feedback.user.username  # get the username throught the feedback relationship

    if not session["username"] == username:
        raise Unauthorized()
    else:
        # we update a feedback for this user

        form = UpdateFeedbackForm(obj=current_feedback)

        if form.validate_on_submit():
            current_feedback.title = form.title.data
            current_feedback.content = form.content.data
            db.session.commit()
            flash('You updated one feedback!')
            return redirect(f'/users/{username}')

        else:
            return render_template(
                "update_feedback.html", form=form, feedback=current_feedback)


@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id: int):
    """ delete the feedback"""

    current_feedback = Feedback.query.filter_by(id=feedback_id).first()
    username = current_feedback.user.username  # get the username throught the feedback relationship

    if not session["username"] == username:
        raise Unauthorized()

    else:
        db.session.delete(current_feedback)
        db.session.commit()

        return redirect(f'/users/{username}')
