from flask import Flask, render_template, request, g, Response, redirect, session, abort, send_file
from flaskext.markdown import Markdown
from jinja2 import FileSystemLoader, ChoiceLoader
from werkzeug.utils import secure_filename
from shutil import rmtree, copyfile

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
from KerbalStuff.objects import User, Mod, Media, ModVersion
from KerbalStuff.helpers import following_mod, following_user
from KerbalStuff.email import send_confirmation
from KerbalStuff.common import get_user, loginrequired, json_output
from KerbalStuff.network import *

app = Flask(__name__)
app.secret_key = _cfg("secret-key")
app.jinja_env.cache = None
Markdown(app, safe_mode='remove')
init_db()

@app.route("/")
def index():
    return render_template("index.html")

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
        user = get_user()
        mods = list()
        for mod in user.mods:
            details = dict()
            details['mod'] = mod
            if len(mod.versions) > 0:
                details['latest_version'] = mod.versions[0]
                details['details'] = '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64]
                details['dl_link'] = '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64] + '/download/' + mod.versions[0].friendly_version
                mods.append(details)
        mods = sorted(mods, key=lambda mod: mod['mod'].created, reverse=True)
        return render_template("profile.html", **{ 'mods': mods, 'following': None })
    else:
        user = get_user()
        user.description = request.form.get('description')
        user.twitterUsername = request.form.get('twitter')
        user.forumUsername = request.form.get('ksp-forum-user')
        user.forumId = int(request.form.get('ksp-forum-id'))
        user.ircNick = request.form.get('irc-nick')
        user.backgroundMedia = request.form.get('backgroundMedia')
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
    mods = list()
    for mod in user.mods:
        details = dict()
        details['mod'] = mod
        if len(mod.versions) > 0:
            details['latest_version'] = mod.versions[0]
            details['safe_name'] = secure_filename(mod.name)[:64]
            details['details'] = '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64]
            details['dl_link'] = '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64] + '/download/' + mod.versions[0].friendly_version
            mods.append(details)
    mods = sorted(mods, key=lambda mod: mod['mod'].created, reverse=True)
    if not current or current.id != mod.user_id:
        mods = [mod for mod in mods if mod['mod'].published]
    return render_template("view_profile.html", **{ 'profile': user, 'mods': mods })

@app.route("/mod/<id>", defaults={'mod_name': None})
@app.route("/mod/<id>/<mod_name>")
def mod(id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == id).first()
    if not mod:
        abort(404)
    if not mod.published and (not user or user.id != mod.user_id):
        abort(401)
    videos = list()
    screens = list()
    latest = mod.versions[0]
    for m in mod.medias:
        if m.type == 'video':
            videos.append(m)
        else:
            screens.append(m)
    return render_template("mod.html",
        **{
            'mod': mod,
            'videos': videos,
            'screens': screens,
            'latest': latest,
            'safe_name': secure_filename(mod.name)[:64]
        })

@app.route('/mod/<mod_id>/<mod_name>/publish')
def publish(mod_id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if not user or user.id != mod.user_id:
        abort(401)
    mod.published = True
    db.commit()
    return redirect('/mod/' + mod_id + '/' + mod_name)

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
    return send_file(os.path.join(_cfg('storage'), version.download_path), as_attachment = True)

@app.route("/create")
@loginrequired
def create_step0():
    return render_template("create/step0.html")

@app.route("/create/mod", methods=['GET', 'POST'])
@loginrequired
def create_mod():
    if request.method == 'GET':
        return render_template("create/step1.html")
    else:
        user = get_user()
        if not user.public:
            # Only public users can create mods
            # /create tells users about this
            return redirect("/create")
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
                mod.media.append(m)
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
        'user': get_user(),
        'len': len,
        'following_mod': following_mod,
        'following_user': following_user
    }
