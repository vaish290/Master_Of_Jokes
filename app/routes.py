from flask import Blueprint, render_template, redirect, url_for, flash, request, abort,current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from . import db
from functools import partial, wraps
from .models import User, Joke, Rating
from .forms import LoginForm, RegistrationForm, JokeForm, RatingForm,EditBalanceForm
import logging



bp = Blueprint('main', __name__)

def moderator_required(f):
    """Decorator to ensure the current user is a moderator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_moderator():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/moderate_users', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderate_users():
    users = User.query.all()
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        user = User.query.get(user_id)
        if action == 'promote':
            user.role = 'Moderator'
            db.session.commit()
            current_app.logger.warning(f"Role changed: {user.nickname} promoted to Moderator.")
        elif action == 'demote' and user.role == 'Moderator':
            # Ensure at least one moderator remains
            if User.query.filter_by(role='Moderator').count() > 1:
                user.role = 'User'
                db.session.commit()
                current_app.logger.warning(f"Role changed: {user.nickname} demoted to User.")
            else:
                flash('Cannot remove the last moderator.')
                return redirect(url_for('main.moderate_users'))
        db.session.commit()
        flash('User roles updated.')
    return render_template('moderate_users.html', users=users)

@bp.route('/edit_balance', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_balance():
    users = User.query.all()
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_balance = request.form.get('new_balance')
        if not user_id or not new_balance:
            current_app.logger.warning("Input validation error: Missing user_id or new_balance.")
            flash("Please provide valid inputs.", "danger")
            return redirect(url_for('main.edit_balance'))
        user = User.query.get(user_id)
        if user:
            user.joke_balance = int(new_balance)
            db.session.commit()
            current_app.logger.info(f"Balance updated for user: {user.nickname}, New Balance: {new_balance}")
            flash(f"Balance updated for {user.nickname}.", "success")
        else:
            current_app.logger.error(f"User not found for ID: {user_id}")
            flash("User not found.", "danger")
        return redirect(url_for('main.edit_balance'))
    return render_template('edit_balance.html', users=users)

@bp.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.jokes'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, nickname=form.nickname.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.jokes'))
    
    return render_template('index.html', title='Welcome', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.jokes'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.email == form.login.data) | (User.nickname == form.login.data)).first()
        if user is None or not user.check_password(form.password.data):
            current_app.logger.warning(f"Authentication failed for login: {form.login.data}")
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user)
        current_app.logger.info(f"Authentication successful for user: {user.nickname}")
        return redirect(url_for('main.jokes'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/jokes')
@login_required
def jokes():
    user_jokes = current_user.jokes.all()
    other_jokes = Joke.query.filter(Joke.user_id != current_user.id).all()
    # Log return values from database queries
    current_app.logger.debug(f"User Jokes: {user_jokes}")
    current_app.logger.debug(f"Other Jokes: {other_jokes}")
    return render_template('jokes.html', title='Jokes', user_jokes=user_jokes, other_jokes=other_jokes)

@bp.route('/leave_joke', methods=['GET', 'POST'])
@login_required
def leave_joke():
    """Allow normal users to leave a joke."""
    if current_user.role == 'Moderator':
        abort(403)  # Moderators cannot leave jokes

    form = JokeForm()
    if form.validate_on_submit():
        joke = Joke(title=form.title.data, body=form.body.data, author=current_user)
        db.session.add(joke)
        current_user.joke_balance += 1
        db.session.commit()
        flash('Your joke has been added!')
        return redirect(url_for('main.jokes'))
    return render_template('leave_joke.html', title='Leave a Joke', form=form)

@bp.route('/view_joke/<int:joke_id>', methods=['GET', 'POST'])
@login_required
def view_joke(joke_id):
    try:
        joke = Joke.query.get_or_404(joke_id)
        
        # Check if the current user has already rated or viewed this joke
        existing_rating = Rating.query.filter_by(user_id=current_user.id, joke_id=joke.id).first()
        
        # If user hasn't rated or viewed this joke before and their balance is 0, redirect them
        if existing_rating is None and current_user.joke_balance == 0:
            current_app.logger.warning("Authorization failure: Insufficient joke balance.")
            flash('You need to leave a joke first before you can view or rate others.')
            return redirect(url_for('main.my_jokes'))
        
        # If user hasn't rated or viewed this joke before, decrement their balance
        if existing_rating is None:
            current_user.joke_balance -= 1
            db.session.commit()

        form = RatingForm()
        
        # Handle rating submission if the user is not the author
        if form.validate_on_submit() and current_user != joke.author:
            if existing_rating:
                existing_rating.value = form.rating.data  # Update existing rating
                current_app.logger.info(f"Rating updated by {current_user.nickname} for joke {joke.title}.")
            else:
                rating = Rating(value=form.rating.data, user_id=current_user.id, joke_id=joke.id)
                db.session.add(rating)
                current_app.logger.info(f"New rating submitted by {current_user.nickname} for joke {joke.title}.")
            
            db.session.commit()
            flash('Your rating has been submitted.')
            return redirect(url_for('main.view_joke', joke_id=joke.id))

        return render_template(
            'view_joke.html',
            title='View Joke',
            joke=joke,
            form=form,
            can_edit=(current_user == joke.author),  # Allow editing only if current user is the author
            can_rate=(current_user != joke.author)   # Allow rating only if current user is not the author
        )
    except Exception as e:
        current_app.logger.error(f"Error while processing view_joke route: {e}", exc_info=True)
        abort(500)  # Trigger Flask's built-in error handler
@bp.route('/edit_joke/<int:joke_id>', methods=['GET', 'POST'])
@login_required
def edit_joke(joke_id):
    joke = Joke.query.get_or_404(joke_id)
    # Ensure that only the author or a moderator can edit jokes
    if current_user != joke.author and not current_user.is_moderator():
        abort(403)

    form = JokeForm()
    if form.validate_on_submit():
        joke.body = form.body.data
        db.session.commit()
        flash('Your joke has been updated.')
        return redirect(url_for('main.jokes'))
    elif request.method == 'GET':
        form.body.data = joke.body

    # Pass the joke object to the template
    return render_template('edit_joke.html', title='Edit Your Joke', form=form, joke=joke)

# Route: Delete Joke (for moderators or authors only)
@bp.route('/delete_joke/<int:joke_id>', methods=['POST'])
@login_required
def delete_joke(joke_id):
    """Allow moderators or authors to delete jokes."""
    joke = Joke.query.get_or_404(joke_id)
    if current_user != joke.author and not current_user.is_moderator():
        abort(403)  # Only the author or moderators can delete jokes

    db.session.delete(joke)
    db.session.commit()
    flash('Joke deleted successfully.', 'success')
    return redirect(url_for('main.jokes'))

@bp.route('/my_jokes')
@login_required
def my_jokes():
    jokes = current_user.jokes.all()  # Get all jokes submitted by the current user
    return render_template('my_jokes.html', title='My Jokes', jokes=jokes)
@bp.route('/take_joke')
@login_required
def take_joke():
    """Allow normal users to take a joke."""
    if current_user.role == 'Moderator':
        abort(403)  # Moderators cannot take jokes

    if current_user.joke_balance > 0:
        joke = Joke.query.filter(Joke.user_id != current_user.id).first()
        if joke:
            flash(f"Here's a joke: {joke.body}", 'info')
            current_user.joke_balance -= 1
            db.session.commit()
            return redirect(url_for('main.jokes'))

    # Render the 'take_joke' template with jokes not authored by the user
    return render_template('take_joke.html', title='Take a Joke', jokes=jokes)
# My Jokes Route - Display
@bp.route('/toggle_debug', methods=['POST'])
@login_required
@moderator_required
def toggle_debug():
    """Allow moderators to toggle debug logging mode."""
    from flask import current_app

    if current_app.logger.level == logging.DEBUG:
        current_app.logger.setLevel(logging.INFO)
        flash("Logging level set to INFO.", "info")
        current_app.logger.info("Logging level changed to INFO.")
    else:
        current_app.logger.setLevel(logging.DEBUG)
        flash("Logging level set to DEBUG.", "info")
        current_app.logger.debug("Logging level changed to DEBUG.")

    return redirect(url_for('main.jokes'))