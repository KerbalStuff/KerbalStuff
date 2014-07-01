from flask import Blueprint, render_template, abort
from KerbalStuff.objects import User
from KerbalStuff.database import db
from KerbalStuff.common import *

profiles = Blueprint('profile', __name__, template_folder='../../templates/profiles')

@profiles.route("/profile/<username>")
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

@profiles.route("/profile", methods=['GET', 'POST'])
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

@profiles.route("/profile/<username>/make-public", methods=['POST'])
@loginrequired
def make_public(username):
    user = get_user()
    if user.username != username:
        abort(401)
    user.public = True
    db.commit()
    return redirect("/profile")
