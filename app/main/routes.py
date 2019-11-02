from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import EditProfileForm
from app.models import User, Laws
from app.main import bp
from app.main.forms import SearchForm
import nltk

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    laws = current_user.followed_laws().paginate(
        page, current_app.config['LAWS_PER_PAGE'], False)
    next_url = url_for('main.index', page=laws.next_num) \
        if laws.has_next else None
    prev_url = url_for('main.index', page=laws.prev_num) \
        if laws.has_prev else None
    return render_template('index.html', title='Home',
                           laws=laws.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    laws = Laws.query.order_by(Laws.timestamp.desc()).paginate(
        page, current_app.config['LAWS_PER_PAGE'], False)
    next_url = url_for('explore', page=laws.next_num) \
        if laws.has_next else None
    prev_url = url_for('explore', page=laws.prev_num) \
        if laws.has_prev else None
    return render_template('index.html', title='Explore', laws=laws.items,
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
    laws = user.laws.order_by(Laws.timestamp.desc()).paginate(
        page, current_app.config['LAWS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=laws.next_num) \
        if laws.has_next else None
    prev_url = url_for('user', username=user.username, page=laws.prev_num) \
        if laws.has_prev else None
    return render_template('user.html', user=user, laws=laws.items,
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


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    laws, total = Laws.search(g.search_form.q.data, page,
                              current_app.config['LAWS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['LAWS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), laws=laws,
                           next_url=next_url, prev_url=prev_url)

@bp.route("/dashboard")
@login_required
def dashboard():
    no_laws = Laws.query.order_by(Laws.timestamp.desc()).count
    return render_template('dashboard.html', no_laws=no_laws)

