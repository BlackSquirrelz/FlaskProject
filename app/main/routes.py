from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import EditProfileForm, SearchForm
from app.models import User, Searches
from app.main import bp

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    searches = current_user.followed_searches().paginate(
        page, current_app.config['SEARCHES_PER_PAGE'], False)
    next_url = url_for('main.index', page=searches.next_num) \
        if searches.has_next else None
    prev_url = url_for('main.index', page=searches.prev_num) \
        if searches.has_prev else None
    return render_template('index.html', title='Home',
                           searches=searches.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    searches = Searches.query.order_by(Searches.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=searches.next_num) \
        if searches.has_next else None
    prev_url = url_for('explore', page=searches.prev_num) \
        if searches.has_prev else None
    return render_template('index.html', title='Explore', posts=searches.items,
                           next_url=next_url, prev_url=prev_url)
@bp.route("/about")
def about():
    return render_template("about.html")

@bp.route("/law_collection")
def law_collection():
    return render_template("law_collection.html")

#USER MANAGEMENT

@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    searches = user.searches.order_by(Searches.timestamp.desc()).paginate(
        page, current_app.config['SEARCHES_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=searches.next_num) \
        if searches.has_next else None
    prev_url = url_for('user', username=user.username, page=searches.prev_num) \
        if searches.has_prev else None
    return render_template('user.html', user=user, searches=searches.items,
                           next_url=next_url, prev_url=prev_url)
#Profile Changes

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

#followers
@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username) not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)!', username=username))
    return redirect(url_for('user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username) not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username).', username=username))
    return redirect(url_for('user', username=username))
