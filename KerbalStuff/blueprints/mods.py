from flask import Blueprint, render_template, request, g, Response, redirect, session, abort, send_file
from sqlalchemy import desc
from KerbalStuff.objects import User, Mod, ModVersion, DownloadEvent, FollowEvent, ReferralEvent, Featured, Media, GameVersion
from KerbalStuff.email import send_update_notification
from KerbalStuff.database import db
from KerbalStuff.common import *
from KerbalStuff.config import _cfg
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from shutil import rmtree, copyfile

import os
import zipfile
import urllib

mods = Blueprint('mods', __name__, template_folder='../../templates/mods')

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
            'thirty_days_ago': thirty_days_ago,
            'share_link': urllib.parse.quote_plus(_cfg("protocol") + "://" + _cfg("domain") + "/mod/" + str(mod.id)),
            'game_versions': GameVersion.query.order_by(desc(GameVersion.id)).all()
        })

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
    base_path = os.path.join(secure_filename(user.username) + '_' + str(user.id), secure_filename(mod.name))
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
    user.following = [m for m in user.following if m.id == mod_id]
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
    return redirect('/mod/' + mod_id + '/' + mod_name)

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

@mods.route('/mod/<mod_id>/<mod_name>/edit_media', methods=['POST'])
@mods.route('/mod/<mod_id>/edit_media', methods=['POST'], defaults={ 'mod_name': None })
@with_session
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
    mod.bgOffsetX = int(bgOffsetX)
    mod.bgOffsetY = int(bgOffsetY)
    return redirect('/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64])

@mods.route('/mod/<mod_id>/<mod_name>/edit_meta', methods=['POST'])
@mods.route('/mod/<mod_id>/edit_meta', methods=['POST'], defaults={ 'mod_name': None })
@with_session
@loginrequired
def edit_meta(mod_id, mod_name):
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
    return redirect('/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64])

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
    return redirect('/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64])

@mods.route("/create/mod", methods=['GET', 'POST'])
@loginrequired
@with_session
def create_mod():
    if request.method == 'GET':
        return render_template("create.html", game_versions=GameVersion.query.order_by(desc(GameVersion.id)).all())
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
        print(ksp_version)
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
            # We'll remove it because the only reason it could be here on creation is an error
            os.remove(path)
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

@mods.route('/mod/<mod_id>/<mod_name>/update', methods=['POST'])
@with_session
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
    if notify:
        send_update_notification(mod)
    db.add(version)
    return redirect('/mod/' + mod_id + '/' + secure_filename(mod.name))
