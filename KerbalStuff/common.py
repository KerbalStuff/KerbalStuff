from flask import session, jsonify
from functools import wraps
from KerbalStuff.objects import User

def get_user():
    if 'user' in session:
        return User.query.filter_by(username=session['user']).first()
    return None
