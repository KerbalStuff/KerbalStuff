from flask import Blueprint, render_template, abort
from flask.ext.login import current_user
from KerbalStuff.objects import User
from KerbalStuff.database import db
from KerbalStuff.common import *

profiles = Blueprint('profile', __name__, template_folder='../../templates/profiles')

@profiles.route("/profile/<username>")
def view_profile(username):
    user = User.query.filter(User.username == username).first()
    if not user:
        abort(404)
    if not user.public:
        if not current_user:
            abort(401)
        if current_user.username != user.username:
            if not current_user.admin:
                abort(401)
    mods_created = sorted(user.mods, key=lambda mod: mod.created, reverse=True)
    if not current_user or current_user.id != user.id:
        mods_created = [mod for mod in mods_created if mod.published]
    mods_followed = sorted(user.following, key=lambda mod: mod.created, reverse=True)
    return render_template("view_profile.html", **{ 'profile': user, 'mods_created': mods_created, 'mods_followed': mods_followed })

@profiles.route("/profile/<username>/edit", methods=['GET', 'POST'])
@loginrequired
@with_session
def profile(username):
    if request.method == 'GET':
        profile = User.query.filter(User.username == username).first()
        if not profile:
            abort(404)
        if current_user != profile and not current_user.admin:
            abort(403)
        return render_template("profile.html", **{ 'profile': profile })
    else:
        profile = User.query.filter(User.username == username).first()
        if not profile:
            abort(404)
        if current_user != profile and not current_user.admin:
            abort(403)
        profile.redditUsername = request.form.get('reddit-username')
        profile.description = request.form.get('description')
        profile.twitterUsername = request.form.get('twitter')
        profile.forumUsername = request.form.get('ksp-forum-user')
        result = getForumId(profile.forumUsername)
        if not result:
            profile.forumUsername = ''
        else:
            profile.forumUsername = result['name']
            profile.forumId = result['id']
        profile.ircNick = request.form.get('irc-nick')
        profile.backgroundMedia = request.form.get('backgroundMedia')
        bgOffsetX = request.form.get('bg-offset-x')
        bgOffsetY = request.form.get('bg-offset-y')
        if bgOffsetX:
            profile.bgOffsetX = int(bgOffsetX)
        if bgOffsetY:
            profile.bgOffsetY = int(bgOffsetY)
        return redirect("/profile/" + profile.username)

@profiles.route("/profile/<username>/make-public", methods=['POST'])
@loginrequired
@with_session
def make_public(username):
    if current_user.username != username:
        abort(401)
    current_user.public = True
    return redirect("/profile/" + current_user.username)
