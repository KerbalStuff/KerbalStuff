from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, ForeignKey, Table, UnicodeText, Text
from sqlalchemy.orm import relationship, backref
from .database import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    username = Column(String(128), nullable = False)
    email = Column(String(256), nullable = False)
    public = Column(Boolean())
    admin = Column(Boolean())
    password = Column(String)
    description = Column(Unicode(4096))
    created = Column(DateTime)
    forumUsername = Column(String(128))
    ircNick = Column(String(128))
    twitterUsername = Column(String(128))
    location = Column(String(128))

    def __init__(self):
        self.following = 0
        self.started = False
        self.finished = False

    def __repr__(self):
        return '<User %r>' % self.username
