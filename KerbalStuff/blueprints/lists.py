from flask import Blueprint, render_template, abort, request, redirect, session
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

@lists.route("/create/list")
def create_list():
    return render_template("create_list.html")

@lists.route("/list/<list_id>/<list_name>")
def view_list(list_id, list_name):
    pass
