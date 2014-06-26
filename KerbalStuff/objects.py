from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, ForeignKey, Table, UnicodeText, Text, text
from sqlalchemy.orm import relationship, backref
from .database import Base

from datetime import datetime
import bcrypt

mod_followers = Table('mod_followers', Base.metadata,
    Column('mod_id', Integer, ForeignKey('mod.id')),
    Column('user_id', Integer, ForeignKey('user.id')),
)

class Featured(Base):
    __tablename__ = 'featured'
    id = Column(Integer, primary_key = True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref=backref('mod', order_by=id))
    created = Column(DateTime)

    def __init__(self):
        self.created = datetime.now()

    def __repr__(self):
        return '<Featured %r>' % self.id

class BlogPost(Base):
    __tablename__ = 'blog'
    id = Column(Integer, primary_key = True)
    title = Column(Unicode(1024))
    text = Column(Unicode(65535))
    created = Column(DateTime)

    def __init__(self):
        self.created = datetime.now()

    def __repr__(self):
        return '<Blog Post %r>' % self.id

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
    following = relationship('Mod', secondary=mod_followers, backref='user.id')

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
    short_description = Column(Unicode(1000))
    approved = Column(Boolean())
    published = Column(Boolean())
    donation_link = Column(String(512))
    external_link = Column(String(512))
    license = Column(String(128))
    votes = Column(Integer())
    created = Column(DateTime)
    updated = Column(DateTime)
    background = Column(String(32))
    medias = relationship('Media')
    versions = relationship('ModVersion', order_by="desc(ModVersion.created)")
    downloads = relationship('DownloadEvent', order_by="desc(DownloadEvent.created)")
    source_link = Column(String(256))
    follower_count = Column(Integer, nullable=False, server_default=text('0'))
    download_count = Column(Integer, nullable=False, server_default=text('0'))
    followers = relationship('User', viewonly=True, secondary=mod_followers, backref='mod.id')

    def __init__(self):
        self.created = datetime.now()
        self.updated = datetime.now()
        self.approved = False
        self.published = False
        self.votes = 0
        self.follower_count = 0
        self.download_count = 0

    def __repr__(self):
        return '<Mod %r %r>' % (self.id, self.name)

class DownloadEvent(Base):
    __tablename__ = 'downloadevent'
    id = Column(Integer, primary_key = True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', viewonly=True, backref=backref('downloadevent', order_by="desc(DownloadEvent.created)"))
    version_id = Column(Integer, ForeignKey('modversion.id'))
    version = relationship('ModVersion', backref=backref('downloadevent', order_by="desc(DownloadEvent.created)"))
    downloads = Column(Integer)
    created = Column(DateTime)

    def __init__(self):
        self.downloads = 0
        self.created = datetime.now()
    
    def __repr__(self):
        return '<Download Event %r>' % self.id

class ModVersion(Base):
    __tablename__ = 'modversion'
    id = Column(Integer, primary_key = True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', viewonly=True, backref=backref('modversion', order_by="desc(ModVersion.created)"))
    friendly_version = Column(String(64))
    ksp_version = Column(String(64))
    created = Column(DateTime)
    download_path = Column(String(512))
    changelog = Column(Unicode(1024))

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
    mod = relationship('Mod', viewonly=True, backref=backref('media', order_by=id))
    hash = Column(String(12))
    type = Column(String(32))
    data = Column(String(512))

    def __init__(self, hash, type, data):
        self.hash = hash
        self.type = type
        self.data = data

    def __repr__(self):
        return '<Media %r>' % self.hash
