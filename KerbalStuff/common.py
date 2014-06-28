from flask import session, jsonify, redirect, request, Response, abort
from werkzeug.utils import secure_filename
from functools import wraps
from KerbalStuff.objects import User

import json
import urllib

def firstparagraph(text):
    try:
        para = text.index("\n\n")
        return text[:para + 2]
    except:
        try:
            para = text.index("\r\n\r\n")
            return text[:para + 4]
        except:
            return text

def remainingparagraphs(text):
    try:
        para = text.index("\n\n")
        return text[para + 2:]
    except:
        try:
            para = text.index("\r\n\r\n")
            return text[para + 4:]
        except:
            return ""

def dumb_object(model):
    if type(model) is list:
        return [dumb_object(x) for x in model]

    result = {}

    for col in model._sa_class_manager.mapper.mapped_table.columns:
        result[col.name] = getattr(model, col.name)

    return result

def wrap_mod(mod):
    details = dict()
    details['mod'] = mod
    if len(mod.versions) > 0:
        details['latest_version'] = mod.versions[0]
        details['safe_name'] = secure_filename(mod.name)[:64]
        details['details'] = '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64]
        details['dl_link'] = '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64] + '/download/' + mod.versions[0].friendly_version
    else:
        return None
    return details

def get_user():
    if 'user' in session:
        return User.query.filter_by(username=session['user']).first()
    return None

def loginrequired(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user()
        if not user or user.confirmation:
            return redirect("/login?return_to=" + urllib.parse.quote_plus(request.url))
        else:
            return f(*args, **kwargs)
    return wrapper

def adminrequired(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user()
        if not user or user.confirmation:
            return redirect("/login?return_to=" + urllib.parse.quote_plus(request.url))
        else:
            if not user.admin:
                abort(401)
            return f(*args, **kwargs)
    return wrapper

def json_output(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        def jsonify_wrap(obj):
            jsonification = json.dumps(obj)
            return Response(jsonification, mimetype='application/json')

        result = f(*args, **kwargs)
        if isinstance(result, tuple):
            return jsonify_wrap(result[0]), result[1]
        if isinstance(result, dict):
            return jsonify_wrap(result)
        if isinstance(result, list):
            return jsonify_wrap(result)

        # This is a fully fleshed out  response, return it immediately
        return result

    return wrapper

def cors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        if request.headers.get('x-cors-status', False):
            if isinstance(res, tuple):
                json_text = res[0].data
                code = res[1]
            else:
                json_text = res.data
                code = 200

            o = json.loads(json_text)
            o['x-status'] = code

            return jsonify(o)

        return res

    return wrapper


