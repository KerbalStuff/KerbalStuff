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
    mods = relationship('Mod', order_by='Mod.created')

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

class Mod(Base):
    __tablename__ = 'mod'
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref=backref('mods', order_by=id))
    name = Column(String(100))
    description = Column(Unicode(100000))
    installation = Column(Unicode(100000))
    approved = Column(Boolean())
    published = Column(Boolean())
    donation_link = Column(String(128))
    external_link = Column(String(128))
    license = Column(String(128))
    keywords = Column(String(256)) # Will do more with this later
    votes = Column(Integer())
    created = Column(DateTime)
    media = relationship('Media')

class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer, primary_key = True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref=backref('media', order_by=id))
    hash = Column(String(12))
    type = Column(String(32))
    data = Column(String(512))
