"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/user/<int:user_id>")
def show_user(user_id):
    """Show a single user with the given user_id"""

    user = User.query.filter(User.user_id == user_id).first()
    user_ratings = user.ratings

    return render_template("user.html", user=user,
                                 user_ratings = user_ratings)


@app.route("/sign_up")
def sign_up():
    """Show form that asks for username and password."""

    return render_template("sign_up.html")

@app.route("/process_sign_up", methods = ['POST'])
def process_sign_up():
    """Process username and password and show success message."""

    new_user_email = request.form.get("email")
    new_user_password = request.form.get("password")

    existing_user = User.query.filter(User.email == new_user_email).all()
    if len(existing_user) > 0:
        return "You're already signed up!"
    else:
        new_user = User(email=new_user_email,
                        password=new_user_password) 
        db.session.add(new_user)
        db.session.commit()
        return "User with email %s signed up successfully" % new_user_email


@app.route("/login")
def login():
    """Allow user to login with username and password."""

    return render_template("login.html")

@app.route("/process_login", methods = ['POST'])
def process_login():
    """Check username and password and redirect if login successful."""

    user_email = request.form.get("email")
    user_password = request.form.get("password")

    existing_user = User.query.filter(User.email == user_email).first()
    if existing_user is None:
        flash("You're not signed up yet. Please sign up!")
        return redirect("/sign_up")
    else:
        if existing_user.password == user_password:
            flash("Successfully logged in!!!!")
            session["user_id"] = existing_user.user_id
            user_id = str(existing_user.user_id)
            return redirect("/user/"+ user_id)
        else:
            flash("Incorrect email/password. Please try again")
            return redirect("/login")


@app.route("/logout")
def logout():
    """Log user out."""

    return render_template("logout.html")


@app.route("/process_logout", methods = ['POST'])
def process_logout():
    """Check username and password and redirect if login successful."""

    del session['user_id'];

    flash("You're now logged out!")
    return redirect("/")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
