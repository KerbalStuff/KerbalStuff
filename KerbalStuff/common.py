from flask import session, jsonify, redirect, request
from functools import wraps
from KerbalStuff.objects import User

import urllib

def get_user():
    if 'user' in session:
        return User.query.filter_by(username=session['user']).first()
    return None

def loginrequired(f):
    # TODO: Handle users who haven't confirmed
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not get_user():
            return redirect("/login?return_to=" + urllib.parse.quote_plus(request.url))
        else:
            return f(*args, **kwargs)
    return wrapper
