from KerbalStuff.common import get_user
from KerbalStuff.objects import User, Mod
from werkzeug.utils import secure_filename

def is_admin():
    user = get_user()
    if not user:
        return False
    return user.admin

def following_mod(mod):
    user = get_user()
    if not user:
        return False
    if any([m.id == mod.id for m in user.following]):
        return True
    return False

def following_user(mod):
    return False
