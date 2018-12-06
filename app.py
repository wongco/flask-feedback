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

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

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

    username = session.get("username")

    if username:
        return redirect(f"/users/{username}")

    form = RegisterForm()

    if form.validate_on_submit():

        # create copy of form dict
        user_form_attr = dict(form.data)

        # remove csrf_token & confirm attribute from user attributes
        del user_form_attr['csrf_token']
        del user_form_attr['confirm']

        # unpack dict properties as keyword arguments for Pet Creation
        user = User.register(**user_form_attr)

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
        flash(f'{user.username} has registed')

        # this is the resource we want to send someone after registering
        return redirect(f"/users/{user.username}")

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


@app.route('/logout')
def logout():
    """ log out the user and clean the session, redirect to main"""

    session.clear()
    return redirect('/')


@app.route('/users/<target_username>')
def display_user_detail(target_username):
    """ display the user details excepts pw """

    if isCurrentUserAuthorized(target_username):
        target_user = User.query.filter_by(username=target_username).first()
        target_feedbacks = target_user.feedbacks
        return render_template('user_details.html', user=target_user, feedbacks=target_feedbacks)

    raise Unauthorized()


@app.route('/users/<target_username>/delete', methods=['POST'])
def delete_user(target_username):
    """ delete the user """

    if isCurrentUserAuthorized(target_username):
        target_user = User.query.filter_by(username=target_username).first()

        db.session.delete(target_user)
        db.session.commit()

        # retrieve current username and if matches target_username, clear session
        current_username = session.get('username')
        if current_username == target_username:
            session.clear()

        return redirect('/')

    raise Unauthorized()


@app.route('/users/<target_username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(target_username):
    """ add feedbacks """

    if isCurrentUserAuthorized(target_username):

        form = AddFeedbackForm()

        if form.validate_on_submit():
            # grab data from the forms
            title = form.title.data
            content = form.content.data

            # created new feedback instance for targeted user and add to db
            new_feedback = Feedback.create_feedback(
                title, content, target_username)
            db.session.add(new_feedback)
            db.session.commit()

            flash('You added one feedback!')

            return redirect(f'/users/{target_username}')

        else:
            return render_template(
                "add_feedback.html", form=form, username=target_username)

    raise Unauthorized()


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id: int):
    """ update feedback details """

    target_feedback = Feedback.query.filter_by(id=feedback_id).first()
    target_username = target_feedback.user.username

    if isCurrentUserAuthorized(target_username):

        form = UpdateFeedbackForm(obj=target_feedback)

        if form.validate_on_submit():
            # grab updated values and add to database
            target_feedback.title = form.title.data
            target_feedback.content = form.content.data
            db.session.commit()

            flash('You updated feedback detail!')

            return redirect(f'/users/{target_username}')

        else:
            return render_template(
                "update_feedback.html", form=form, feedback=target_feedback)

    raise Unauthorized()


@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id: int):
    """ delete the feedback"""

    target_feedback = Feedback.query.filter_by(id=feedback_id).first()
    target_username_str = target_feedback.user.username

    if isCurrentUserAuthorized(target_username_str):

        db.session.delete(target_feedback)
        db.session.commit()

        return redirect(f'/users/{target_username_str}')

    raise Unauthorized()


def isCurrentUserAuthorized(target_username_str):
    """Takes user instances and determines if current user is authorized"""

    current_username = session.get('username')

    # current_username has a value
    if current_username:
        # obtain current_username instance
        current_user = User.query.filter_by(
            username=current_username).first()
        # check if target user is current user or if current user is an admin
        return current_username == target_username_str or current_user.is_admin

    return False


@app.errorhandler(404)
def page_not_found(error):
    """ 404 Handler for Flask """
    return render_template('/404.html'), 404


@app.errorhandler(401)
def user_unauthorized(error):
    """ 401 Handler for Flask """
    return render_template('/401.html'), 401
