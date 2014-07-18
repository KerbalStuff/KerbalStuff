from flask import Blueprint, render_template, abort
from sqlalchemy import desc
from KerbalStuff.objects import User, Mod, GameVersion
from KerbalStuff.database import db
from KerbalStuff.common import *
from KerbalStuff.email import send_bulk_email

admin = Blueprint('admin', __name__, template_folder='../../templates/admin')

@admin.route("/admin")
@adminrequired
def backend():
    users = User.query.count()
    new_users = User.query.order_by(desc(User.created)).limit(24)
    mods = Mod.query.count()
    versions = GameVersion.query.order_by(desc(GameVersion.id)).all()
    return render_template("admin.html", users=users, mods=mods, new_users=new_users, versions=versions)

@admin.route("/versions/create", methods=['POST'])
@adminrequired
@with_session
def create_version():
    friendly = request.form.get("friendly_version")
    if not friendly:
        return redirect("/asdf")
    if any(GameVersion.query.filter(GameVersion.friendly_version == friendly)):
        return redirect("/fsda")
    version = GameVersion(friendly)
    db.add(version)
    db.commit()
    return redirect("/admin")

@admin.route("/admin/email", methods=['POST'])
@adminrequired
def email():
    subject = request.form.get('subject')
    body = request.form.get('body')
    modders_only = request.form.get('modders-only') == 'on'
    if not subject or not body:
        abort(400)
    if subject == '' or body == '':
        abort(400)
    users = User.query.all()
    if modders_only:
        users = [u for u in users if len(u.mods) != 0]
    send_bulk_email([u.email for u in users], subject, body)
    return redirect("/admin")
