from flask import (Blueprint, render_template, abort, request, redirect,
                   session, url_for)
from sqlalchemy import desc
from KerbalStuff.search import search_mods, search_users
from KerbalStuff.objects import *
from KerbalStuff.common import *
from KerbalStuff.config import _cfg
from KerbalStuff.email import send_update_notification

import os
import zipfile
import urllib

api = Blueprint('api', __name__)

default_description = """This is your mod listing! You can edit it as much as you like before you make it public.

To edit **this** text, you can click on the "**Edit this Mod**" button up there.

By the way, you have a lot of flexibility here. You can embed YouTube videos or screenshots. Be creative.

You can check out the Kerbal Stuff [markdown documentation](/markdown) for tips.

Thanks for hosting your mod on Kerbal Stuff!"""

#some helper functions to keep things consistant
def user_info(user):
    return {
        "username": user.username,
        "description": user.description,
        "forumUsername": user.forumUsername,
        "ircNick": user.ircNick,
        "twitterUsername": user.twitterUsername,
        "redditUsername": user.redditUsername
    }

def mod_info(mod):
    return {
        "name": mod.name,
        "id": mod.id,
        "short_description": mod.short_description,
        "downloads": mod.download_count,
        "followers": mod.follower_count,
        "author": mod.user.username,
        "default_version_id": mod.default_version().id
    }

def version_info(mod, version):
    return {
        "friendly_version": version.friendly_version,
        "ksp_version": version.ksp_version,
        "id": version.id,
        "download_path": url_for('mods.download', mod_id=mod.id,
                                 mod_name=mod.name,
                                 version=version.friendly_version),
        "changelog": version.changelog
    }

@api.route("/api/search/mod")
@json_output
def search_mod():
    query = request.args.get('query')
    page = request.args.get('page')
    query = '' if not query else query
    page = 1 if not page or not page.isdigit() else int(page)
    results = list()
    for m in search_mods(query, page, 30)[0]:
        a = mod_info(m)
        a['versions'] = list()
        for v in m.versions:
            a['versions'].append(version_info(m, v))
        results.append(a)
    return results

@api.route("/api/search/user")
@json_output
def search_user():
    query = request.args.get('query')
    page = request.args.get('page')
    query = '' if not query else query
    page = 0 if not page or not page.isdigit() else int(page)
    results = list()
    for u in search_users(query, page):
        a = user_info(u)
        a['mods'] = list()
        mods = Mod.query.filter(Mod.user == u, Mod.published == True).order_by(
            Mod.created)
        for m in mods:
            a['mods'].append(mod_info(m))
        results.append(a)
    return results

@api.route("/api/mod/<modid>")
@json_output
def mod(modid):
    if not modid.isdigit():
        abort(400)
    mod = Mod.query.filter(Mod.id == modid).first()
    if not mod:
        abort(404)
    if not mod.published:
        abort(401)
    info = mod_info(mod)
    info["versions"] = list()
    for v in mod.versions:
        info["versions"].append(version_info(mod, v))
    return info

@api.route("/api/mod/<modid>/<version>")
@json_output
def mod_version(modid, version):
    if not modid.isdigit():
        abort(400)
    mod = Mod.query.filter(Mod.id == modid).first()
    if not mod:
        abort(404)
    if not mod.published:
        abort(401)
    if version == "latest" or version == "latest_version":
        v = mod.default_version()
    elif version.isdigit():
        v = ModVersion.query.filter(ModVersion.mod == mod,
                                    ModVersion.id == int(version)).first()
    else:
        abort(400)
    if not v:
        abort(404)
    info = version_info(mod, v)
    return info

@api.route("/api/user/<username>")
@json_output
def user(username):
    user = User.query.filter(User.username == username).first()
    if not user:
        abort(404)
    if not user.public:
        abort(401)
    mods = Mod.query.filter(Mod.user == user, Mod.published == True).order_by(
        Mod.created)
    info = user_info(user)
    info['mods'] = list()
    for m in mods:
        info['mods'].append(mod_info(m))
    return info

@api.route('/api/mod/create', methods=['POST'])
@json_output
def create_mod():
    user = get_user()
    if not user.public:
        return { 'error': True, 'message': 'Only users with public profiles may create mods.' }, 403
    name = request.form.get('name')
    short_description = request.form.get('short-description')
    version = request.form.get('version')
    ksp_version = request.form.get('ksp-version')
    license = request.form.get('license')
    zipball = request.files.get('zipball')
    # Validate
    if not name \
        or not short_description \
        or not version \
        or not ksp_version \
        or not license \
        or not zipball:
        return { 'error': True, 'message': 'All fields are required.' }, 400
    # Validation, continued
    if len(name) > 100 \
        or len(short_description) > 1000 \
        or len(license) > 128:
        return { 'error': True, 'message': 'Fields exceed maximum permissible length.' }, 400
    mod = Mod()
    mod.user = user
    mod.name = name
    mod.short_description = short_description
    mod.description = default_description
    mod.license = license
    # Save zipball
    filename = secure_filename(name) + '-' + secure_filename(version) + '.zip'
    base_path = os.path.join(secure_filename(user.username) + '_' + str(user.id), secure_filename(name))
    full_path = os.path.join(_cfg('storage'), base_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    path = os.path.join(full_path, filename)
    if os.path.isfile(path):
        # We already have this version
        # We'll remove it because the only reason it could be here on creation is an error
        os.remove(path)
    zipball.save(path)
    if not zipfile.is_zipfile(path):
        os.remove(path)
        return { 'error': True, 'message': 'This is not a valid zip file.' }, 400
    version = ModVersion(secure_filename(version), ksp_version, os.path.join(base_path, filename))
    mod.versions.append(version)
    db.add(version)
    # Save database entry
    db.add(mod)
    db.commit()
    mod.default_version_id = version.id
    return { 'url': url_for("mods.mod", id=mod.id, mod_name=mod.name) }

@api.route('/api/mod/<mod_id>/update', methods=['POST'])
@with_session
@json_output
def update_mod(mod_id):
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
    version = request.form.get('version')
    changelog = request.form.get('changelog')
    ksp_version = request.form.get('ksp-version')
    notify = request.form.get('notify-followers')
    zipball = request.files.get('zipball')
    if not version \
        or not ksp_version \
        or not zipball:
        # Client side validation means that they're just being pricks if they
        # get here, so we don't need to show them a pretty error message
        abort(400)
    if notify == None:
        notify = False
    else:
        notify = notify.lower() == "on"
    filename = secure_filename(mod.name) + '-' + secure_filename(version) + '.zip'
    base_path = os.path.join(secure_filename(user.username) + '_' + str(user.id), secure_filename(mod.name))
    full_path = os.path.join(_cfg('storage'), base_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    path = os.path.join(full_path, filename)
    if os.path.isfile(path):
        return { 'error': True, 'message': 'We already have this version. Did you mistype the version number?' }, 400
    zipball.save(path)
    if not zipfile.is_zipfile(path):
        os.remove(path)
        return { 'error': True, 'message': 'This is not a valid zip file.' }, 400
    version = ModVersion(secure_filename(version), ksp_version, os.path.join(base_path, filename))
    version.changelog = changelog
    # Assign a sort index
    version.sort_index = max([v.sort_index for v in mod.versions]) + 1
    mod.versions.append(version)
    if notify:
        send_update_notification(mod, version)
    db.add(version)
    db.commit()
    mod.default_version_id = version.id
    return { 'url': url_for("mods.mod", id=mod.id, mod_name=mod.name) }
