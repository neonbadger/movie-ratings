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


@app.route("/movies")
def show_movie_list():
    """Display list of all movies, with links to movie detail pages"""

    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movie_list.html", movies=movies)


@app.route("/movie/<int:movie_id>")
def show_movie(movie_id):
    """Show info about a movie and allow user to rate the movie."""

    movie = Movie.query.get(movie_id)
    movie_ratings = movie.ratings

    user_id = session.get("user_id")
    if user_id:
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()
    else:
        user_rating = None

    count = len(movie_ratings)
    if count > 0:
        total = 0
        for rating in movie_ratings:
            total += rating.score
        avg_rating = float(total)/count
    else:
        avg_rating = "This movie has not yet been rated."

    prediction = None

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)


    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction
    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score
    else:
        # User hasn't scored, and we couldn't get a prediction
        effective_rating = None

    # Get the eye's rating, either by predicting or using real rating
    the_eye = User.query.filter_by(email="the-eye@of-judgment.com").one()
    eye_rating = Rating.query.filter_by(
        user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)
    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)
    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has brought me" +
            " to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    if difference is not None:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None


    return render_template("movie.html", movie=movie,
                            movie_ratings=movie_ratings,
                            avg_rating=avg_rating,
                            user_rating=user_rating,
                            prediction=prediction,
                            beratement=beratement)

@app.route("/process_rating", methods = ['POST'])
def process_rating():
    """Add or update user rating to database."""

    rating = request.form.get("new_rating")
    user_id = session["user_id"]
    movie_id = request.form.get("movie_id")

    existing_rating = Rating.query.filter(Rating.user_id == user_id, 
                                          Rating.movie_id == movie_id).all()

    if len(existing_rating) == 0:
        new_rating = Rating(score = rating,
                            user_id = user_id,
                            movie_id = movie_id)
        db.session.add(new_rating)
    
    else:
        existing_rating[0].score = rating

    db.session.commit()

    return "Your rating was submitted."




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
