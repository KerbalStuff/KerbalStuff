from flask import Blueprint, render_template, abort
from sqlalchemy import desc
from KerbalStuff.objects import User, Mod, GameVersion
from KerbalStuff.database import db
from KerbalStuff.common import *
from KerbalStuff.versions import game_versions, load_versions

admin = Blueprint('admin', __name__, template_folder='../../templates/admin')

@admin.route("/admin")
@adminrequired
def backend():
    users = User.query.count()
    new_users = User.query.order_by(desc(User.created)).limit(24)
    mods = Mod.query.count()
    return render_template("admin.html", users=users, mods=mods, new_users=new_users, versions=game_versions)

@admin.route("/versions/create", methods=['POST'])
@adminrequired
@with_session
def create_version():
    friendly = request.form.get("friendly_version")
    if not friendly:
        return redirect("/asdf")
    if any([v for v in game_versions if v.friendly_version == friendly]):
        return redirect("/fsda")
    print(friendly)
    version = GameVersion(friendly)
    print(version)
    db.add(version)
    db.commit()
    print("done")
    load_versions()
    return redirect("/admin")
