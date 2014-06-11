from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, ForeignKey, Table, UnicodeText, Text
from sqlalchemy.orm import relationship, backref
from .database import Base

from datetime import datetime
import bcrypt

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    username = Column(String(128), nullable = False, index = True)
    email = Column(String(256), nullable = False, index = True)
    public = Column(Boolean())
    admin = Column(Boolean())
    password = Column(String)
    description = Column(Unicode(10000))
    created = Column(DateTime)
    forumUsername = Column(String(128))
    forumId = Column(Integer)
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
    user = relationship('User', backref=backref('mod', order_by=id))
    name = Column(String(100), index = True)
    description = Column(Unicode(100000), index = True)
    installation = Column(Unicode(100000))
    approved = Column(Boolean())
    published = Column(Boolean())
    donation_link = Column(String(512))
    external_link = Column(String(512))
    license = Column(String(128))
    votes = Column(Integer())
    created = Column(DateTime)
    background = Column(String(32))
    medias = relationship('Media')
    versions = relationship('ModVersion')
    source_link = Column(String(256))

    def __init__(self):
        self.created = datetime.now()
        self.approved = False
        self.published = False
        self.votes = 0

    def __repr__(self):
        return '<Mod %r>' % self.name

class ModVersion(Base):
    __tablename__ = 'modversion'
    id = Column(Integer, primary_key = True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref=backref('modversion', order_by="ModVersion.created"))
    friendly_version = Column(String(64))
    ksp_version = Column(String(64))
    created = Column(DateTime)
    download_path = Column(String(512))

    def __init__(self, friendly_version, ksp_version, download_path):
        self.friendly_version = friendly_version
        self.ksp_version = ksp_version
        self.download_path = download_path
        self.created = datetime.now()

    def __repr__(self):
        return '<Mod Version %r>' % self.id

class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer, primary_key = True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref=backref('media', order_by=id))
    hash = Column(String(12))
    type = Column(String(32))
    data = Column(String(512))

    def __init__(self, hash, type, data):
        self.hash = hash
        self.type = type
        self.data = data

    def __repr__(self):
        return '<Media %r>' % self.hash
