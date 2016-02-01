from flask import Blueprint, render_template, request, redirect, session
from flask import url_for, current_app
from flask.ext.login import current_user, login_user
from flask_oauthlib.client import OAuth
from KerbalStuff.config import _cfg
from KerbalStuff.email import send_confirmation
from KerbalStuff.objects import User, UserAuth
from KerbalStuff.database import db
from KerbalStuff.blueprints.accounts import check_username_for_registration, check_email_for_registration
import os
import binascii
from collections import OrderedDict

login_oauth = Blueprint('login_oauth', __name__)

@login_oauth.route("/login-oauth", methods=['GET', 'POST'])
def login_with_oauth():
    if request.method == 'GET':
        return redirect('/login')
    provider = request.form.get('provider')

    if not is_oauth_provider_configured(provider):
        return 'This install is not configured for login with %s' % provider

    if provider == 'github':
        github = get_provider_github()
        callback = url_for('.login_with_oauth_authorized_github', _external=True)
        return github.authorize(callback=callback)

    else:
        return 'Unknown oauth provider %s' % provider


@login_oauth.route("/connect-oauth", methods=['POST'])
def connect_with_oauth():
    provider = request.form.get('provider')

    if not is_oauth_provider_configured(provider):
        return 'This install is not configured for login with %s' % provider

    if provider == 'github':
        github = get_provider_github()
        callback = url_for('.connect_with_oauth_authorized_github', _external=True)
        return github.authorize(callback=callback)

    else:
        return 'Unknown oauth provider %s' % provider

@login_oauth.route("/disconnect-oauth", methods=['POST'])
def disconnect_oauth():
    provider = request.form.get('provider')

    assert provider in list_defined_oauths()  # This is a quick and dirty form of sanitation.

    auths = UserAuth.query.filter(UserAuth.provider == provider, UserAuth.user_id == current_user.id).all()
    for auth in auths:
        db.delete(auth)

    db.flush()  # So that /profile will display currectly
    return redirect('/profile/%s/edit' % current_user.username)

@login_oauth.route("/oauth/github/connect")     # other providers will use /oauth/<provider>/<action>
def connect_with_oauth_authorized_github():
    if 'code' not in request.args:
        # Got here in some strange scenario.
        return redirect('/')
    github = get_provider_github()
    resp = github.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    if 'error' in resp:
        return jsonify(resp)
    session['github_token'] = (resp['access_token'], '')
    gh_info = github.get('user')
    gh_info = gh_info.data
    gh_user = gh_info['login']

    if not current_user:
        return 'Trying to associate an account, but not logged in?'

    auth = UserAuth.query.filter(UserAuth.provider == 'github', UserAuth.remote_user == gh_user).first()
    if auth:
        if auth.user_id == current_user.id:
            # You're already set up.
            return redirect('/profile/%s/edit' % current_user.username)

        # This account is already connected with some user.
        return 'Your GitHub account is already connected to a KerbalStuff account.'

    auth = UserAuth(current_user.id, gh_user, 'github')
    db.add(auth)
    db.flush()  # So that /profile will display currectly

    return redirect('/profile/%s/edit' % current_user.username)

@login_oauth.route("/oauth/github/login")
def login_with_oauth_authorized_github():
    if 'code' not in request.args:
        # Got here in some strange scenario.
        return redirect('/')
    github = get_provider_github()
    resp = github.authorized_response()

    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    if 'error' in resp:
        return jsonify(resp)
    session['github_token'] = (resp['access_token'], '')
    gh_info = github.get('user')
    gh_info = gh_info.data
    gh_user = gh_info['login']
    auth = UserAuth.query.filter(UserAuth.provider == 'github', UserAuth.remote_user == gh_user).first()
    if auth:
        user = User.query.filter(User.id == auth.user_id).first()
        if user.confirmation:
            return redirect('/account-pending')
        login_user(user, remember=True)
        return redirect('/')
    else:
        emails = github.get('user/emails')
        emails = emails.data
        emails = [e['email'] for e in emails if e['primary']]
        if emails:
            email = emails[0]
        else:
            email = ''

        return render_register_with_oauth('github', gh_user, gh_user, email)


@login_oauth.route("/register-oauth", methods=['POST'])
def register_with_oauth_authorized():
    '''
    This endpoint should be called after authorizing with oauth, by the user.
    '''
    email = request.form.get('email')
    username = request.form.get('username')
    provider = request.form.get('provider')
    remote_user = request.form.get('remote_user')

    good = True
    if check_username_for_registration(username):
        good = False
    if check_email_for_registration(email):
        good = False

    if good:
        password = binascii.b2a_hex(os.urandom(99))
        user = User(username, email, password)
        user.confirmation = binascii.b2a_hex(os.urandom(20)).decode("utf-8")
        db.add(user)
        db.flush()  # to get an ID.
        auth = UserAuth(user.id, remote_user, provider)
        db.add(auth)
        db.commit()  # Commit before trying to email

        send_confirmation(user)
        return redirect("/account-pending")

    return render_register_with_oauth(provider, remote_user, username, email)


def render_register_with_oauth(provider, remote_user, username, email):
    provider_info = list_defined_oauths()[provider]

    parameters = {
        'email': email, 'username': username,
        'provider': provider,
        'provider_full_name': provider_info['full_name'],
        'provider_icon': provider_info['icon'],
        'remote_user': remote_user,
    }

    error = check_username_for_registration(username)
    if error:
        parameters['usernameError'] = error

    error = check_email_for_registration(email)
    if error:
        parameters['emailError'] = error

    return render_template('register-oauth.html', **parameters)


def get_provider_github():
    oauth = OAuth(current_app)
    github = oauth.remote_app(
        'github',
        consumer_key=_cfg('gh-oauth-id'),
        consumer_secret=_cfg('gh-oauth-secret'),
        request_token_params={'scope': 'user:email'},
        base_url='https://api.github.com/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize'
    )

    @github.tokengetter
    def get_github_oauth_token():
        return session.get('github_token')

    return github

def list_connected_oauths(user):
    auths = UserAuth.query.filter(UserAuth.user_id == user.id).all()
    return [a.provider for a in auths]

DEFINED_OAUTHS = None
def list_defined_oauths():
    global DEFINED_OAUTHS
    if DEFINED_OAUTHS is not None:
        return DEFINED_OAUTHS

    master_list = OrderedDict()
    master_list['github'] = {
        'full_name': 'GitHub',
        'icon': 'github',
    }
    master_list['google'] = {
        'full_name': 'Google',
        'icon': 'google',
    }
    master_list['facebook'] = {
        'full_name': 'Facebook',
        'icon': 'facebook-official',
    }

    for p in list(master_list.keys()):
        if not is_oauth_provider_configured(p):
            del master_list[p]

    DEFINED_OAUTHS = master_list
    return DEFINED_OAUTHS

def is_oauth_provider_configured(provider):
    if provider == 'github':
        return bool(_cfg('gh-oauth-id')) and bool(_cfg('gh-oauth-secret'))
    return False
