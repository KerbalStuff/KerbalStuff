import sys

from KerbalStuff.config import _cfg, _cfgi
from KerbalStuff.database import db, init_db
from KerbalStuff.objects import User
from KerbalStuff.email import send_confirmation

init_db()

if sys.argv[1] == 'delete_user':
    user = User.query.filter(User.username == sys.argv[2]).first()
    if not user:
        sys.exit("User not found.")
    else:
        db.delete(user)
        db.commit()
        print("Success.")
        sys.exit()
