from KerbalStuff.objects import User
from KerbalStuff.database import db
from KerbalStuff.common import getForumId

affected = User.query.filter(User.forumId == None)

for user in affected:
    if User.forumUsername:
        result = getForumId(user.forumUsername)
        if not result:
            user.forumUsername = ''
        else:
            user.forumUsername = result['name']
            user.forumId = result['id']
        db.commit()
