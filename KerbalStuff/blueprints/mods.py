from flask import Blueprint, render_template, request, g, Response, redirect, session, abort, send_file, make_response, url_for
from sqlalchemy import desc
from KerbalStuff.objects import User, Mod, ModVersion, DownloadEvent, FollowEvent, ReferralEvent, Featured, Media, GameVersion
from KerbalStuff.email import send_update_notification, send_autoupdate_notification
from KerbalStuff.database import db
from KerbalStuff.common import *
from KerbalStuff.config import _cfg
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from shutil import rmtree, copyfile
from urllib.parse import urlparse

import os
import zipfile
import urllib

mods = Blueprint('mods', __name__, template_folder='../../templates/mods')

@mods.route("/mod/<id>/<mod_name>/update")
def update(id, mod_name):
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
    return render_template("update.html", mod=mod, game_versions=GameVersion.query.order_by(desc(GameVersion.id)).all())

@mods.route("/mod/<id>", defaults={'mod_name': None})
@mods.route("/mod/<id>/<mod_name>")
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
    latest = mod.default_version()
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
    if request.args.get('noedit') != None:
        editable = False
    forumThread = False
    if mod.external_link != None:
        try:
            u = urlparse(mod.external_link)
            if u.netloc == 'forum.kerbalspaceprogram.com':
                forumThread = True
        except e:
            print(e)
            pass
    return render_template("mod.html",
        **{
            'mod': mod,
            'latest': latest,
            'safe_name': secure_filename(mod.name)[:64],
            'featured': any(Featured.query.filter(Featured.mod_id == mod.id).all()),
            'editable': editable,
            'download_stats': download_stats,
            'follower_stats': follower_stats,
            'referrals': referrals,
            'json_versions': json_versions,
            'thirty_days_ago': thirty_days_ago,
            'share_link': urllib.parse.quote_plus(_cfg("protocol") + "://" + _cfg("domain") + "/mod/" + str(mod.id)),
            'game_versions': GameVersion.query.order_by(desc(GameVersion.id)).all(),
            'forum_thread': forumThread,
            'new': request.args.get('new') != None
        })

@mods.route("/mod/<id>/<mod_name>/edit", methods=['GET', 'POST'])
@with_session
def edit_mod(id, mod_name):
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
    if request.method == 'GET':
        return render_template("edit_mod.html", mod=mod)
    else:
        short_description = request.form.get('short-description')
        license = request.form.get('license')
        donation_link = request.form.get('donation-link')
        external_link = request.form.get('external-link')
        source_link = request.form.get('source-link')
        description = request.form.get('description')
        background = request.form.get('background')
        bgOffsetY = request.form.get('bg-offset-y')
        if not license or license == '':
            return render_template("edit_mod.html", mod=mod, error="All mods must have a license.")
        mod.short_description = short_description
        mod.license = license
        mod.donation_link = donation_link
        mod.external_link = external_link
        mod.source_link = source_link
        mod.description = description
        if background and background != '':
            mod.background = background
        try:
            mod.bgOffsetY = int(bgOffsetY)
        except:
            pass
        return redirect(url_for("mods.mod", id=mod.id, mod_name=mod.name))

@mods.route("/create/mod")
@loginrequired
@with_session
def create_mod():
    return render_template("create.html", game_versions=GameVersion.query.order_by(desc(GameVersion.id)).all())

@mods.route("/mod/<mod_id>/stats/downloads", defaults={'mod_name': None})
@mods.route("/mod/<mod_id>/<mod_name>/stats/downloads")
def export_downloads(mod_id, mod_name):
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
    download_stats = DownloadEvent.query\
        .filter(DownloadEvent.mod_id == mod.id)\
        .order_by(DownloadEvent.created)
    response = make_response(render_template("downloads.csv", stats=download_stats))
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment;filename=downloads.csv'
    return response

@mods.route("/mod/<mod_id>/stats/followers", defaults={'mod_name': None})
@mods.route("/mod/<mod_id>/<mod_name>/stats/followers")
def export_followers(mod_id, mod_name):
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
    follower_stats = FollowEvent.query\
        .filter(FollowEvent.mod_id == mod.id)\
        .order_by(FollowEvent.created)
    response = make_response(render_template("followers.csv", stats=follower_stats))
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment;filename=followers.csv'
    return response

@mods.route("/mod/<mod_id>/stats/referrals", defaults={'mod_name': None})
@mods.route("/mod/<mod_id>/<mod_name>/stats/referrals")
def export_referrals(mod_id, mod_name):
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
    referral_stats = ReferralEvent.query\
            .filter(ReferralEvent.mod_id == mod.id)\
            .order_by(desc(ReferralEvent.events))
    response = make_response(render_template("referrals.csv", stats=referral_stats))
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment;filename=referrals.csv'
    return response

@mods.route("/mod/<mod_id>/delete", methods=['POST'])
@loginrequired
@with_session
def delete(mod_id):
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
    db.delete(mod)
    for feature in Featured.query.filter(Featured.mod_id == mod.id).all():
        db.delete(feature)
    for media in Media.query.filter(Media.mod_id == mod.id).all():
        db.delete(media)
    for version in ModVersion.query.filter(ModVersion.mod_id == mod.id).all():
        db.delete(version)
    db.commit()
    base_path = os.path.join(secure_filename(mod.user.username) + '_' + str(mod.user.id), secure_filename(mod.name))
    full_path = os.path.join(_cfg('storage'), base_path)
    rmtree(full_path)
    return redirect("/profile/" + user.username)

@mods.route("/mod/<mod_id>/follow", methods=['POST'])
@loginrequired
@json_output
@with_session
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
    return { "success": True }

@mods.route("/mod/<mod_id>/unfollow", methods=['POST'])
@loginrequired
@json_output
@with_session
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
    user.following = [m for m in user.following if m.id != int(mod_id)]
    return { "success": True }

@mods.route('/mod/<mod_id>/feature', methods=['POST'])
@adminrequired
@json_output
@with_session
def feature(mod_id):
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if any(Featured.query.filter(Featured.mod_id == mod_id).all()):
        abort(409)
    feature = Featured()
    feature.mod = mod
    db.add(feature)
    return { "success": True }

@mods.route('/mod/<mod_id>/unfeature', methods=['POST'])
@adminrequired
@json_output
@with_session
def unfeature(mod_id):
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    feature = Featured.query.filter(Featured.mod_id == mod_id).first()
    if not feature:
        abort(404)
    db.delete(feature)
    return { "success": True }

@mods.route('/mod/<mod_id>/<mod_name>/publish')
@with_session
def publish(mod_id, mod_name):
    user = get_user()
    mod = Mod.query.filter(Mod.id == mod_id).first()
    if not mod:
        abort(404)
    if not user or user.id != mod.user_id:
        abort(401)
    mod.published = True
    mod.updated = datetime.now()
    return redirect(url_for("mods.mod", id=mod.id, mod_name=mod.name))

@mods.route('/mod/<mod_id>/download/<version>', defaults={ 'mod_name': None })
@mods.route('/mod/<mod_id>/<mod_name>/download/<version>')
@with_session
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
    return send_file(os.path.join(_cfg('storage'), version.download_path), as_attachment = True)

@mods.route('/mod/<mod_id>/version/<version_id>/delete', methods=['POST'])
@with_session
@loginrequired
def delete_version(mod_id, version_id):
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
    version = [v for v in mod.versions if v.id == int(version_id)]
    if len(mod.versions) == 1:
        abort(400)
    if len(version) == 0:
        abort(404)
    if version[0].id == mod.default_version_id:
        abort(400)
    db.delete(version[0])
    mod.versions = [v for v in mod.versions if v.id != int(version_id)]
    db.commit()
    return redirect(url_for("mods.mod", id=mod.id, mod_name=mod.name))


@mods.route('/mod/<mod_id>/<mod_name>/edit_version', methods=['POST'])
@mods.route('/mod/<mod_id>/edit_version', methods=['POST'], defaults={ 'mod_name': None })
@with_session
@loginrequired
def edit_version(mod_name, mod_id):
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
    version_id = int(request.form.get('version-id'))
    changelog = request.form.get('changelog')
    version = [v for v in mod.versions if v.id == version_id]
    if len(version) == 0:
        abort(404)
    version = version[0]
    version.changelog = changelog
    return redirect(url_for("mods.mod", id=mod.id, mod_name=mod.name))

@mods.route('/mod/<mod_id>/set-default/<v_id>', methods=['POST'])
@with_session
@loginrequired
def set_default_version(mod_id, v_id):
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
    mod.default_version_id = v_id
    return redirect(url_for("mods.mod", id=mod.id, mod_name=mod.name))

@mods.route('/mod/<mod_id>/autoupdate', methods=['POST'])
@with_session
def autoupdate(mod_id):
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
    default = mod.default_version()
    default.ksp_version = GameVersion.query.order_by(desc(GameVersion.id)).first().friendly_version
    send_autoupdate_notification(mod)
    return redirect(url_for("mods.mod", id=mod.id, mod_name=mod.name))
