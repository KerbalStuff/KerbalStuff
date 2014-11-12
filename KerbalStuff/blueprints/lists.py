from flask import Blueprint, render_template, abort, request, redirect, session, url_for
from flask.ext.login import current_user, login_user, logout_user
from datetime import datetime, timedelta
from KerbalStuff.email import send_confirmation, send_reset
from KerbalStuff.objects import User, Mod, ModList, ModListItem
from KerbalStuff.database import db
from KerbalStuff.common import *

import bcrypt
import re
import random
import base64
import binascii
import os

lists = Blueprint('lists', __name__, template_folder='../../templates/lists')

@lists.route("/create/pack")
def create_list():
    return render_template("create_list.html")

@lists.route("/pack/<list_id>/<list_name>")
def view_list(list_id, list_name):
    mod_list = ModList.query.filter(ModList.id == list_id).first()
    if not mod_list:
        abort(404)
    editable = False
    if current_user:
        if current_user.admin:
            editable = True
        if current_user.id == mod_list.user_id:
            editable = True
    return render_template("mod_list.html",
        **{
            'mod_list': mod_list,
            'editable': editable
        })

@lists.route("/pack/<list_id>/<list_name>/edit", methods=['GET', 'POST'])
@with_session
@loginrequired
def edit_list(list_id, list_name):
    mod_list = ModList.query.filter(ModList.id == list_id).first()
    if not mod_list:
        abort(404)
    editable = False
    if current_user:
        if current_user.admin:
            editable = True
        if current_user.id == mod_list.user_id:
            editable = True
    if not editable:
        abort(401)
    if request.method == 'GET':
        return render_template("edit_list.html",
            **{
                'mod_list': mod_list
            })
    else:
        description = request.form.get('description')
        background = request.form.get('background')
        bgOffsetY = request.form.get('bg-offset-y')
        mod_list.description = description
        if background and background != '':
            mod_list.background = background
        try:
            mod_list.bgOffsetY = int(bgOffsetY)
        except:
            pass
        return redirect(url_for("lists.view_list", list_id=mod_list.id, list_name=mod_list.name))
