from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, ForeignKey, Table, UnicodeText, Text
from sqlalchemy.orm import relationship, backref
from .database import Base

from datetime import datetime
import bcrypt
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    username = Column(String(128), nullable = False)
    email = Column(String(256), nullable = False)
    public = Column(Boolean())
    admin = Column(Boolean())
    password = Column(String)
    description = Column(Unicode(10000))
    created = Column(DateTime)
    forumUsername = Column(String(128))
    ircNick = Column(String(128))
    twitterUsername = Column(String(128))
    location = Column(String(128))
    confirmation = Column(String(128))
    backgroundMedia = Column(String(32))

    def __init__(self, username, email, password):
        self.email = email
        self.username = username
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())
        self.public = False
        self.admin = False
        self.created = datetime.now()
        self.twitterUsername = ''
        self.forumUsername = ''
        self.ircNick = ''
        self.description = ''
        self.backgroundMedia = ''

    def __repr__(self):
        return '<User %r>' % self.username
