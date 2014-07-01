from flask import Blueprint, render_template, abort
from sqlalchemy import desc
from KerbalStuff.objects import User, Mod
from KerbalStuff.database import db
from KerbalStuff.common import *

admin = Blueprint('admin', __name__, template_folder='../../templates/admin')

@admin.route("/admin")
@adminrequired
def backend():
    users = User.query.count()
    new_users = User.query.order_by(desc(User.created)).limit(24)
    mods = Mod.query.count()
    return render_template("admin.html", users=users, mods=mods, new_users=new_users)
