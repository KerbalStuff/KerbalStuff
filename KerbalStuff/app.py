from flask import Flask, render_template, request, g, Response, redirect, session, abort, send_file
from flaskext.markdown import Markdown
from jinja2 import FileSystemLoader, ChoiceLoader
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from shutil import rmtree, copyfile
from werkzeug.utils import secure_filename
from sqlalchemy import desc

import os
import traceback
import subprocess
import random
import re
import base64
import bcrypt
import urllib
import requests
import binascii
import json
import zipfile
import xml.etree.ElementTree as ET

from KerbalStuff.config import _cfg, _cfgi
from KerbalStuff.database import db, init_db
from KerbalStuff.objects import *
from KerbalStuff.helpers import following_mod, following_user, is_admin
from KerbalStuff.email import send_confirmation, send_update_notification, send_reset
from KerbalStuff.common import get_user, loginrequired, json_output, wrap_mod, adminrequired, firstparagraph, remainingparagraphs, dumb_object
from KerbalStuff.search import search_mods
from KerbalStuff.network import *
from KerbalStuff.custom_json import CustomJSONEncoder
from KerbalStuff.kerbdown import KerbDown

app = Flask(__name__)
app.jinja_env.filters['firstparagraph'] = firstparagraph
app.jinja_env.filters['remainingparagraphs'] = remainingparagraphs
app.secret_key = _cfg("secret-key")
app.jinja_env.cache = None
app.json_encoder = CustomJSONEncoder
markdown = Markdown(app, safe_mode='remove', extensions=[KerbDown()])
init_db()

@app.route("/")
def index():
    featured = Featured.query.order_by(desc(Featured.created)).limit(7)[:7]
    blog = BlogPost.query.order_by(desc(BlogPost.created)).all()
    return render_template("index.html", featured=featured, blog=blog)

@app.route("/browse")
def browse():
    featured = Featured.query.order_by(desc(Featured.created)).limit(7)[:7]
    top = search_mods("", 0)[:7]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(7)[:7]
    return render_template("browse.html", featured=featured, top=top, new=new)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/markdown")
def markdown_info():
    return render_template("markdown.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/admin")
@adminrequired
def admin():
    users = User.query.count()
    new_users = User.query.order_by(desc(User.created)).limit(24)
    mods = Mod.query.count()
    return render_template("admin.html", users=users, mods=mods, new_users=new_users)

@app.route("/blog/post", methods=['POST'])
@adminrequired
def post_blog():
    title = request.form.get('post-title')
    body = request.form.get('post-body')
    post = BlogPost()
    post.title = title
    post.text = body
    db.add(post)
    db.commit()
    return redirect("/blog/" + str(post.id))

@app.route("/blog/<id>/edit", methods=['GET', 'POST'])
@adminrequired
def edit_blog(id):
    post = BlogPost.query.filter(BlogPost.id == id).first()
    if not post:
        abort(404)
    if request.method == 'GET':
        return render_template("edit_blog.html", post=post)
    else:
        title = request.form.get('post-title')
        body = request.form.get('post-body')
        post.title = title
        post.text = body
        db.commit()
        return redirect("/blog/" + str(post.id))

@app.route("/blog/<id>/delete", methods=['POST'])
@adminrequired
@json_output
def delete_blog(id):
    post = BlogPost.query.filter(BlogPost.id == id).first()
    if not post:
        abort(404)
    db.delete(post)
    db.commit()
    return redirect("/")

@app.route("/blog/<id>")
def blog(id):
    post = BlogPost.query.filter(BlogPost.id == id).first()
    if not post:
        abort(404)
    return render_template("blog.html", post=post)

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
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                kwargs['emailError'] = 'Please specify a valid email address.'
            elif db.query(User).filter(User.email == email).first():
                kwargs['emailError'] = 'A user with this email already exists.'
        if not username:
            kwargs['usernameError'] = 'Username is required.'
        else:
            if not re.match(r"^[A-Za-z0-9_]+$", username):
                kwargs['usernameError'] = 'Please only use letters, numbers, and underscores.'
            if len(username) < 3 or len(username) > 24:
                kwargs['usernameError'] = 'Usernames must be between 3 and 24 characters.'
            if db.query(User).filter(User.username == username).first():
                kwargs['usernameError'] = 'A user by this name already exists.'
        if not password:
            kwargs['passwordError'] = 'Password is required.'
        else:
            if password != confirmPassword:
                kwargs['repeatPasswordError'] = 'Passwords do not match.'
            if len(password) < 5:
                kwargs['passwordError'] = 'Your password must be greater than 5 characters.'
            if len(password) > 256:
                kwargs['passwordError'] = 'We admire your dedication to security, but please use a shorter password.'
        if not kwargs == dict():
            if email is not None:
                kwargs['email'] = email
            if username is not None:
                kwargs['username'] = username
            return render_template("register.html", **kwargs)
        # All valid, let's make them an account
        user = User(username, email, password)
        user.confirmation = binascii.b2a_hex(os.urandom(20)).decode("utf-8")
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
        reset = request.args.get('reset') == '1'
        return render_template("login.html", **{ 'return_to': request.args.get('return_to'), 'reset': reset })
    else:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template("login.html", **{ "username": username, "errors": 'Your username or password is incorrect.' })
        if user.confirmation != '' and user.confirmation != None:
            return redirect("/account-pending")
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

@app.route("/forgot-password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template("forgot.html")
    else:
        email = request.form.get('email')
        if not email:
            return render_template("forgot.html", bad_email=True)
        user = User.query.filter(User.email == email).first()
        if not user:
            return render_template("forgot.html", bad_email=True, email=email)
        user.passwordReset = binascii.b2a_hex(os.urandom(20)).decode("utf-8")
        user.passwordResetExpiry = datetime.now() + timedelta(days=1)
        send_reset(user)
        db.commit()
        return render_template("forgot.html", success=True)

@app.route("/reset", methods=['GET', 'POST'])
@app.route("/reset/<username>/<confirmation>", methods=['GET', 'POST'])
def reset_password(username, confirmation):
    user = User.query.filter(User.username == username).first()
    if not user:
        redirect("/")
    if request.method == 'GET':
        if user.passwordResetExpiry == None or user.passwordResetExpiry < datetime.now():
            return render_template("reset.html", expired=True)
        if user.passwordReset != confirmation:
            redirect("/")
        return render_template("reset.html", username=username, confirmation=confirmation)
    else:
        if user.passwordResetExpiry == None or user.passwordResetExpiry < datetime.now():
            abort(401)
        if user.passwordReset != confirmation:
            abort(401)
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if not password or not password2:
            return render_template("reset.html", username=username, confirmation=confirmation, errors="Please fill out both fields.")
        if password != password2:
            return render_template("reset.html", username=username, confirmation=confirmation, errors="You seem to have mistyped one of these, please try again.")
        user.set_password(password)
        user.passwordReset = None
        user.passwordResetExpiry = None
        db.commit()
        return redirect("/login?reset=1")

@app.route("/profile", methods=['GET', 'POST'])
@loginrequired
def profile():
    if request.method == 'GET':
        user = get_user()
        mods = list()
        for mod in user.mods:
            m = wrap_mod(mod)
            if m:
                mods.append(m)
        mods = sorted(mods, key=lambda m: m['mod'].created, reverse=True)
        return render_template("profile.html", **{ 'mods': mods, 'following': None })
    else:
        user = get_user()
        user.redditUsername = request.form.get('reddit-username')
        user.description = request.form.get('description')
        user.twitterUsername = request.form.get('twitter')
        user.forumUsername = request.form.get('ksp-forum-user')
        forumId = request.form.get('ksp-forum-id')
        if forumId:
            user.forumId = int(forumId)
        else:
            result = getForumId(user.forumUsername)
            if not result:
                user.forumUsername = ''
            else:
                user.forumUsername = result['name']
                user.forumId = result['id']
        user.ircNick = request.form.get('irc-nick')
        user.backgroundMedia = request.form.get('backgroundMedia')
        bgOffsetX = request.form.get('bg-offset-x')
        bgOffsetY = request.form.get('bg-offset-y')
        if bgOffsetX:
            user.bgOffsetX = int(bgOffsetX)
        if bgOffsetY:
            user.bgOffsetY = int(bgOffsetY)
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
        if not current:
            abort(401)
        if current.username != user.username:
            if not current.admin:
                abort(401)
    mods_created = sorted(user.mods, key=lambda mod: mod.created, reverse=True)
    if not current or current.id != user.id:
        mods_created = [mod for mod in mods_created if mod.published]
    mods_followed = sorted(user.following, key=lambda mod: mod.created, reverse=True)
    return render_template("view_profile.html", **{ 'profile': user, 'mods_created': mods_created, 'mods_followed': mods_followed })

@app.route("/mod/<id>", defaults={'mod_name': None})
@app.route("/mod/<id>/<mod_name>")
def mod(id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == id).first()
    if not mod:
        abort(404)
    editable = False
    if user:
        if user.admin:
            editable = True
        if user.id == mod.user_id:
            editable = True
    if not mod.published and not editable:
        abort(401)
    videos = list()
    screens = list()
    latest = mod.versions[0]
    screenshot_list = ",".join([s.data for s in mod.media if s.type == 'image'])
    video_list = ",".join([s.data for s in mod.media if s.type == 'video'])
    for m in mod.medias:
        if m.type == 'video':
            videos.append(m)
        else:
            screens.append(m)
    referral = request.referrer
    if referral:
        host = urllib.parse.urlparse(referral).hostname
        event = ReferralEvent.query\
                .filter(ReferralEvent.mod_id == mod.id)\
                .filter(ReferralEvent.host == host)\
                .first()
        if not event:
            event = ReferralEvent()
            event.mod = mod
            event.events = 1
            event.host = host
            mod.referrals.append(event)
            db.add(event)
        else:
            event.events += 1
        db.commit()
    download_stats = None
    follower_stats = None
    referrals = None
    json_versions = None
    thirty_days_ago = datetime.now() - timedelta(days=30)
    if editable:
        referrals = list()
        for r in ReferralEvent.query\
            .filter(ReferralEvent.mod_id == mod.id)\
            .order_by(desc(ReferralEvent.events)):
            referrals.append( { 'host': r.host, 'count': r.events } )
        download_stats = list()
        for d in DownloadEvent.query\
            .filter(DownloadEvent.mod_id == mod.id)\
            .filter(DownloadEvent.created > thirty_days_ago)\
            .order_by(DownloadEvent.created):
            download_stats.append(dumb_object(d))
        follower_stats = list()
        for f in FollowEvent.query\
            .filter(FollowEvent.mod_id == mod.id)\
            .filter(FollowEvent.created > thirty_days_ago)\
            .order_by(FollowEvent.created):
            follower_stats.append(dumb_object(f))
        json_versions = list()
        for v in mod.versions:
            json_versions.append({ 'name': v.friendly_version, 'id': v.id })
    return render_template("mod.html",
        **{
            'mod': mod,
            'videos': videos,
            'screens': screens,
            'latest': latest,
            'safe_name': secure_filename(mod.name)[:64],
            'featured': any(Featured.query.filter(Featured.mod_id == mod.id).all()),
            'editable': editable,
            'screenshot_list': screenshot_list,
            'video_list': video_list,
            'download_stats': download_stats,
            'follower_stats': follower_stats,
            'referrals': referrals,
            'json_versions': json_versions,
            'thirty_days_ago': thirty_days_ago
        })

@app.route("/mod/<mod_id>/delete", methods=['POST'])
@loginrequired
def delete(mod_id):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if not admin or not user.id == mod.user.id:
        abort(401)

    db.delete(mod)
    for feature in Featured.query.filter(Featured.mod_id == mod.id).all():
        db.delete(feature)
    for media in Media.query.filter(Media.mod_id == mod.id).all():
        db.delete(media)
    for version in ModVersion.query.filter(ModVersion.mod_id == mod.id).all():
        db.delete(version)
    base_path = os.path.join(secure_filename(user.username) + '_' + str(user.id), secure_filename(mod.name))
    full_path = os.path.join(_cfg('storage'), base_path)
    rmtree(full_path)

    db.commit()
    return redirect("/profile")

@app.route("/mod/<mod_id>/follow", methods=['POST'])
@loginrequired
@json_output
def follow(mod_id):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if any(m.id == mod.id for m in user.following):
        abort(418)
    event = FollowEvent.query\
            .filter(FollowEvent.mod_id == mod.id)\
            .order_by(desc(FollowEvent.created))\
            .first()
    # Events are aggregated hourly
    if not event or ((datetime.now() - event.created).seconds / 60 / 60) >= 1:
        event = FollowEvent()
        event.mod = mod
        event.delta = 1
        event.events = 1
        mod.follow_events.append(event)
        db.add(event)
    else:
        event.delta += 1
        event.events += 1
    mod.follower_count += 1
    user.following.append(mod)
    db.commit()
    return { "success": True }

@app.route("/mod/<mod_id>/unfollow", methods=['POST'])
@loginrequired
@json_output
def unfollow(mod_id):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if not any(m.id == mod.id for m in user.following):
        abort(418)
    event = FollowEvent.query\
            .filter(FollowEvent.mod_id == mod.id)\
            .order_by(desc(FollowEvent.created))\
            .first()
    # Events are aggregated hourly
    if not event or ((datetime.now() - event.created).seconds / 60 / 60) >= 1:
        event = FollowEvent()
        event.mod = mod
        event.delta = -1
        event.events = 1
        mod.follow_events.append(event)
        db.add(event)
    else:
        event.delta -= 1
        event.events += 1
    mod.follower_count -= 1
    user.following = [m for m in user.following if m.id == mod_id]
    db.commit()
    return { "success": True }

@app.route('/mod/<mod_id>/feature', methods=['POST'])
@adminrequired
@json_output
def feature(mod_id):
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if any(Featured.query.filter(Featured.mod_id == mod_id).all()):
        abort(409)
    feature = Featured()
    feature.mod = mod
    db.add(feature)
    db.commit()
    return { "success": True }

@app.route('/mod/<mod_id>/unfeature', methods=['POST'])
@adminrequired
@json_output
def unfeature(mod_id):
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    feature = Featured.query.filter(Featured.mod_id == mod_id).first()
    if not feature:
        abort(404)
    db.delete(feature)
    db.commit()
    return { "success": True }

@app.route('/mod/<mod_id>/<mod_name>/publish')
def publish(mod_id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if not user or user.id != mod.user_id:
        abort(401)
    mod.published = True
    mod.updated = datetime.now()
    db.commit()
    return redirect('/mod/' + mod_id + '/' + mod_name)

@app.route('/mod/<mod_id>/download/<version>', defaults={ 'mod_name': None })
@app.route('/mod/<mod_id>/<mod_name>/download/<version>')
def download(mod_id, mod_name, version):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if not mod.published and (not user or user.id != mod.user_id):
        abort(401)
    version = ModVersion.query.filter(ModVersion.mod_id == mod_id, \
            ModVersion.friendly_version == version).first()
    if not version:
        abort(404)
    download = DownloadEvent.query\
            .filter(DownloadEvent.mod_id == mod.id and DownloadEvent.version_id == version.id)\
            .order_by(desc(DownloadEvent.created))\
            .first()
    # Events are aggregated hourly
    if not download or ((datetime.now() - download.created).seconds / 60 / 60) >= 1:
        download = DownloadEvent()
        download.mod = mod
        download.version = version
        download.downloads = 1
        mod.downloads.append(download)
        db.add(download)
    else:
        download.downloads += 1
    mod.download_count += 1
    db.commit()
    return send_file(os.path.join(_cfg('storage'), version.download_path), as_attachment = True)

@app.route('/mod/<mod_id>/<mod_name>/edit_media', methods=['POST'])
@app.route('/mod/<mod_id>/edit_media', methods=['POST'], defaults={ 'mod_name': None })
def edit_media(mod_id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    editable = False
    if user:
        if user.admin:
            editable = True
        if user.id == mod.user_id:
            editable = True
    if not editable:
        abort(401)
    screenshots = request.form.get('screenshots')
    videos = request.form.get('videos')
    background = request.form.get('backgroundMedia')
    bgOffsetX = request.form.get('bg-offset-x')
    bgOffsetY = request.form.get('bg-offset-y')
    screenshot_list = screenshots.split(',')
    video_list = videos.split(',')
    if len(screenshot_list) > 5 \
        or len(video_list) > 2 \
        or len(background) > 32:
        abort(400)
    [db.delete(m) for m in mod.media]
    for screenshot in screenshot_list:
        if screenshot:
            r = requests.get('https://mediacru.sh/' + screenshot + '.json')
            if r.status_code != 200:
                abort(400)
            j = r.json()
            data = ''
            if j['blob_type'] == 'image':
                for f in j['files']:
                    if f['type'] == 'image/jpeg' or f['type'] == 'image/png':
                        data = f['file']
            else:
                abort(400)
            m = Media(j['hash'], j['blob_type'], data)
            mod.medias.append(m)
    for video in video_list:
        if video:
            r = requests.get('https://mediacru.sh/' + video + '.json')
            if r.status_code != 200:
                abort(400)
            j = r.json()
            data = ''
            if j['blob_type'] == 'video':
                data = j['hash']
            else:
                abort(400)
            m = Media(j['hash'], j['blob_type'], data)
            mod.medias.append(m)
            db.add(m)
    mod.background = background
    mod.bgOffsetX = bgOffsetX
    mod.bgOffsetY = bgOffsetY
    db.commit()
    return redirect('/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64])

@app.route('/mod/<mod_id>/<mod_name>/edit_meta', methods=['POST'])
@app.route('/mod/<mod_id>/edit_meta', methods=['POST'], defaults={ 'mod_name': None })
def edit_meta(mod_id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    editable = False
    if user:
        if user.admin:
            editable = True
        if user.id == mod.user_id:
            editable = True
    if not editable:
        abort(401)
    name = request.form.get('name')
    description = request.form.get('description')
    short_description = request.form.get('short-description')
    external_link = request.form.get('external-link')
    license = request.form.get('license')
    source_link = request.form.get('source-code')
    donation_link = request.form.get('donation')
    if not short_description \
        or not description \
        or not license:
        # TODO: Better error
        abort(400)
    if len(description) > 100000 \
        or len(donation_link) > 512 \
        or len(external_link) > 512 \
        or len(license) > 128 \
        or len(source_link) > 256:
        abort(400)
    mod.description = description
    mod.short_description = short_description
    mod.external_link = external_link
    mod.license = license
    mod.source_link = source_link
    mod.donation_link = donation_link
    db.commit()
    return redirect('/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64])

@app.route("/search")
def search():
    query = request.args.get('query')
    results = search_mods(query, 0)
    wrapped = list()
    for result in results:
        m = wrap_mod(result)
        if m:
            wrapped.append(m)
    return render_template("search.html", results=wrapped, query=query)

@app.route("/create/mod", methods=['GET', 'POST'])
@loginrequired
def create_mod():
    if request.method == 'GET':
        return render_template("create.html")
    else:
        user = get_user()
        if not user.public:
            # Only public users can create mods
            # /create tells users about this
            return redirect("/create/mod")
        name = request.form.get('name')
        description = request.form.get('description')
        short_description = request.form.get('short-description')
        version = request.form.get('version')
        ksp_version = request.form.get('ksp-version')
        external_link = request.form.get('external-link')
        license = request.form.get('license')
        source_link = request.form.get('source-code')
        donation_link = request.form.get('donation')
        screenshots = request.form.get('screenshots')
        videos = request.form.get('videos')
        background = request.form.get('backgroundMedia')
        zipball = request.files.get('zipball')
        # Validate
        if not name \
            or not short_description \
            or not description \
            or not version \
            or not ksp_version \
            or not license \
            or not zipball:
            # Client side validation means that they're just being pricks if they
            # get here, so we don't need to show them a pretty error message
            abort(400)
        screenshot_list = screenshots.split(',')
        video_list = videos.split(',')
        # Validation, continued
        if len(name) > 100 \
            or len(description) > 100000 \
            or len(donation_link) > 512 \
            or len(external_link) > 512 \
            or len(license) > 128 \
            or len(source_link) > 256 \
            or len(background) > 32 \
            or len(screenshot_list) > 5 \
            or len(video_list) > 2:
            abort(400)
        mod = Mod()
        mod.user = user
        mod.name = name
        mod.description = description
        mod.short_description = short_description
        mod.external_link = external_link
        mod.license = license
        mod.source_link = source_link
        mod.donation_link = donation_link
        mod.background = background
        # Do media
        for screenshot in screenshot_list:
            if screenshot:
                r = requests.get('https://mediacru.sh/' + screenshot + '.json')
                if r.status_code != 200:
                    abort(400)
                j = r.json()
                data = ''
                if j['blob_type'] == 'image':
                    for f in j['files']:
                        if f['type'] == 'image/jpeg' or f['type'] == 'image/png':
                            data = f['file']
                else:
                    abort(400)
                m = Media(j['hash'], j['blob_type'], data)
                mod.medias.append(m)
        for video in video_list:
            if video:
                r = requests.get('https://mediacru.sh/' + video + '.json')
                if r.status_code != 200:
                    abort(400)
                j = r.json()
                data = ''
                if j['blob_type'] == 'video':
                    data = j['hash']
                else:
                    abort(400)
                m = Media(j['hash'], j['blob_type'], data)
                mod.medias.append(m)
                db.add(m)
        # Save zipball
        filename = secure_filename(name) + '-' + secure_filename(version) + '.zip'
        base_path = os.path.join(secure_filename(user.username) + '_' + str(user.id), secure_filename(name))
        full_path = os.path.join(_cfg('storage'), base_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        path = os.path.join(full_path, filename)
        if os.path.isfile(path):
            # We already have this version
            # TODO: Error message
            abort(400)
        zipball.save(path)
        if not zipfile.is_zipfile(path):
            os.remove(path)
            abort(400) # TODO: Error message
        version = ModVersion(secure_filename(version), ksp_version, os.path.join(base_path, filename))
        mod.versions.append(version)
        db.add(version)
        # Save database entry
        db.add(mod)
        db.commit()
        return redirect('/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64])

@app.route('/mod/<mod_id>/<mod_name>/update', methods=['GET', 'POST'])
def update(mod_id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    editable = False
    if user:
        if user.admin:
            editable = True
        if user.id == mod.user_id:
            editable = True
    if not editable:
        abort(401)
    if request.method == 'GET':
        return render_template("update.html", **{ 'mod': mod })
    else:
        version = request.form.get('version')
        changelog = request.form.get('changelog')
        ksp_version = request.form.get('ksp-version')
        zipball = request.files.get('zipball')
        if not version \
            or not ksp_version \
            or not zipball:
            # Client side validation means that they're just being pricks if they
            # get here, so we don't need to show them a pretty error message
            abort(400)
        filename = secure_filename(mod.name) + '-' + secure_filename(version) + '.zip'
        base_path = os.path.join(secure_filename(user.username) + '_' + str(user.id), secure_filename(mod.name))
        full_path = os.path.join(_cfg('storage'), base_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        path = os.path.join(full_path, filename)
        if os.path.isfile(path):
            # We already have this version
            # TODO: Error message
            abort(400)
        zipball.save(path)
        if not zipfile.is_zipfile(path):
            os.remove(path)
            abort(400) # TODO: Error message
        version = ModVersion(secure_filename(version), ksp_version, os.path.join(base_path, filename))
        version.changelog = changelog
        mod.versions.append(version)
        send_update_notification(mod)
        db.add(version)
        db.commit()
        return redirect('/mod/' + mod_id + '/' + secure_filename(mod.name))

@app.route('/ksp-profile-proxy/<fragment>')
@json_output
def profile_proxy(fragment):
    r = requests.post("http://forum.kerbalspaceprogram.com/ajax.php?do=usersearch", data= {
        'securitytoken': 'guest',
        'do': 'usersearch',
        'fragment': fragment
        })
    root = ET.fromstring(r.text)
    results = list()
    for child in root:
        results.append({
            'id': child.attrib['userid'],
            'name': child.text
        })
    return results

@app.route('/version')
def version():
    return Response(subprocess.check_output(["git", "log", "-1"]), mimetype="text/plain")

@app.route('/hook', methods=['POST'])
def hook_publish():
    print("Hook recieved")
    allow = False
    for ip in _cfg("hook_ips").split(","):
        parts = ip.split("/")
        range = 32
        if len(parts) != 1:
            range = int(parts[1])
        addr = networkMask(parts[0], range)
        if addressInNetwork(dottedQuadToNum(request.remote_addr), addr):
            allow = True
    if not allow:
        print("Hook ignored - not whitelisted IP")
        abort(403)
    print("Hook permitted")
    # Pull and restart site
    event = json.loads(request.data.decode("utf-8"))
    if not _cfg("hook_repository") == "%s/%s" % (event["repository"]["owner"]["name"], event["repository"]["name"]):
        return "ignored"
    if any("[noupdate]" in c["message"] for c in event["commits"]):
        return "ignored"
    if "refs/heads/" + _cfg("hook_branch") == event["ref"]:
        print("Updating on hook")
        subprocess.call(["git", "pull", "origin", "master"])
        subprocess.call(_cfg("restart_command").split())
        return "thanks"
    return "ignored"

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

@app.context_processor
def inject():
    ads = True
    first_visit = True
    if 'ad-opt-out' in request.cookies:
        ads = False
    if g.do_not_track:
        ads = False
    if not _cfg("project_wonderful_id"):
        ads = False
    if request.cookies.get('first_visit') != None:
        first_visit = False
    return {
        'mobile': g.mobile,
        'ua_platform': request.user_agent.platform,
        'analytics_id': _cfg("google_analytics_id"),
        'analytics_domain': _cfg("google_analytics_domain"),
        'disqus_id': _cfg("disqus_id"),
        'dnt': g.do_not_track,
        'ads': ads,
        'ad_id': _cfg("project_wonderful_id"),
        'root': _cfg("protocol") + "://" + _cfg("domain"),
        'domain': _cfg("domain"),
        'user': get_user(),
        'len': len,
        'any': any,
        'following_mod': following_mod,
        'following_user': following_user,
        'bgindex': random.choice(range(0, 11)),
        'admin': is_admin(),
        'wrap_mod': wrap_mod,
        'dumb_object': dumb_object,
        'first_visit': first_visit
    }
