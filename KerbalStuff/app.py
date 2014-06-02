from flask import Flask, render_template, request, g, Response, redirect, session, abort
from flaskext.markdown import Markdown
from jinja2 import FileSystemLoader, ChoiceLoader

import os
import traceback
import subprocess
import random
import re
import base64
import bcrypt
import urllib

from KerbalStuff.config import _cfg, _cfgi
from KerbalStuff.database import db, init_db
from KerbalStuff.objects import User
from KerbalStuff.email import send_confirmation
from KerbalStuff.common import get_user, loginrequired

app = Flask(__name__)
app.secret_key = _cfg("secret-key")
app.jinja_env.cache = None
Markdown(app, safe_mode='remove')
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mod/<id>")
def mod(id):
    return render_template("mod.html")

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # Validate
        kwargs = dict()
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirmPassword = request.form.get('repeatPassword')
        if not email:
            kwargs['emailError'] = 'Email is required.'
        else:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                kwargs['emailError'] = 'Please specify a valid email address.'
            elif db.query(User).filter(User.email == email).first():
                kwargs['emailError'] = 'A user with this email already exists.'
        if not username:
            kwargs['usernameError'] = 'Username is required.'
        else:
            if db.query(User).filter(User.username == username).first():
                kwargs['usernameError'] = 'A user by this name already exists.'
        if not password:
            kwargs['passwordError'] = 'Password is required.'
        else:
            if password != confirmPassword:
                kwargs['repeatPasswordError'] = 'Passwords do not match.'
        if not kwargs == dict():
            if email is not None:
                kwargs['email'] = email
            if username is not None:
                kwargs['username'] = username
            return render_template("register.html", **kwargs)
        # All valid, let's make them an account
        user = User(username, email, password)
        user.confirmation = base64.urlsafe_b64encode(os.urandom(20))
        db.add(user)
        db.commit()
        send_confirmation(user)
        return redirect("/account-pending")
    else:
        return render_template("register.html")

@app.route("/account-pending")
def account_pending():
    return render_template("account-pending.html")

@app.route("/confirm/<username>/<confirmation>")
def confirm(username, confirmation):
    user = User.query.filter(User.username == username).first()
    if user and user.confirmation == None:
        return redirect("/")
    if not user or user.confirmation != confirmation:
        return render_template("confirm.html", **{ 'success': False, 'user': user })
    else:
        user.confirmation = None
        db.commit()
        session['user'] = user.username
        return render_template("confirm.html", **{ 'success': True, 'user': user })

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if get_user():
            return redirect("/")
        return render_template("login.html", **{ 'return_to': request.args.get('return_to') })
    else:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template("login.html", **{ "username": username, "errors": 'Your username or password is incorrect.' })
        if not bcrypt.checkpw(password, user.password):
            return render_template("login.html", **{ "username": username, "errors": 'Your username or password is incorrect.' })
        session['user'] = user.username
        if 'return_to' in request.form and request.form['return_to']:
            return redirect(urllib.parse.unquote(request.form.get('return_to')))
        return redirect("/")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect("/")

@app.route("/profile", methods=['GET', 'POST'])
@loginrequired
def profile():
    if request.method == 'GET':
        return render_template("profile.html")
    else:
        user = get_user()
        user.description = request.form.get('description')
        user.twitterUsername = request.form.get('twitter')
        user.forumUsername = request.form.get('ksp-forums')
        user.ircNick = request.form.get('irc-nick')
        user.backgroundMedia = request.form.get('backgroundMedia')
        print(user.description)
        db.commit()
        return redirect("/profile")

@app.route("/profile/<username>/make-public", methods=['POST'])
@loginrequired
def make_public(username):
    user = get_user()
    if user.username != username:
        abort(401)
    user.public = True
    db.commit()
    return redirect("/profile")

@app.route("/profile/<username>")
def view_profile(username):
    user = User.query.filter(User.username == username).first()
    current = get_user()
    if not user:
        abort(404)
    if not user.public:
        if not current or current.username != user.username:
            abort(401)
    return render_template("view_profile.html", **{ 'profile': user })

@app.before_request
def find_dnt():
    field = "Dnt"
    do_not_track = False
    if field in request.headers:
        do_not_track = True if request.headers[field] == "1" else False
    g.do_not_track = do_not_track

@app.before_request
def jinja_template_loader():
    mobile = request.user_agent.platform in ['android', 'iphone', 'ipad'] \
           or 'windows phone' in request.user_agent.string.lower() \
           or 'mobile' in request.user_agent.string.lower()
    g.mobile = mobile
    if mobile:
        app.jinja_loader = ChoiceLoader([
            FileSystemLoader(os.path.join("templates", "mobile")),
            FileSystemLoader("templates"),
        ])
    else:
        app.jinja_loader = FileSystemLoader("templates")

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", error="File not found."), 404

@app.errorhandler(Exception)
def exception_catch_all(e):
    traceback.print_exc()
    return render_template("error.html", error=repr(e)), 500

@app.context_processor
def inject():
    ads = True
    if 'ad-opt-out' in request.cookies:
        ads = False
    if g.do_not_track:
        ads = False
    if not _cfg("project_wonderful_id"):
        ads = False
    return {
        'mobile': g.mobile,
        'ua_platform': request.user_agent.platform,
        'analytics_id': _cfg("google_analytics_id"),
        'analytics_domain': _cfg("google_analytics_domain"),
        'ads': ads,
        'ad_id': _cfg("project_wonderful_id"),
        'root': _cfg("protocol") + "://" + _cfg("domain"),
        'domain': _cfg("domain"),
        'user': get_user()
    }
