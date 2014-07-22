from flask import (Blueprint, render_template, abort, request, redirect,
                   session, url_for)
from sqlalchemy import desc
from KerbalStuff.search import search_mods, search_users
from KerbalStuff.objects import *
from KerbalStuff.common import *

api = Blueprint('api', __name__)

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
    page = 0 if not page or not page.isdigit() else int(page)
    results = list()
    for m in search_mods(query, page):
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
    if version == "latest":
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
