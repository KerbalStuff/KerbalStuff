from flask import Blueprint, render_template, abort, request, redirect, session, Response
from flask.ext.login import current_user
from sqlalchemy import desc
from KerbalStuff.objects import Featured, BlogPost, Mod
from KerbalStuff.search import search_mods
from KerbalStuff.common import *
from KerbalStuff.config import _cfg

import praw
import math

anonymous = Blueprint('anonymous', __name__, template_folder='../../templates/anonymous')
r = praw.Reddit(user_agent="SpaceDock")

@anonymous.route("/anniversary")
def anniversary():
    user_count = User.query.count()
    mod_count = Mod.query.count()
    download_count = 0
    top = search_mods("", 1, 6)[0]
    oldest = Mod.query.filter(Mod.published).order_by(Mod.created).limit(6)[:6]
    for m in Mod.query.all():
        download_count += m.download_count
    return render_template("anniversary.html", users=user_count, \
            mods=mod_count, downloads=download_count, top=top, oldest=oldest, site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/")
def index():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 3)[0]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(3)[:3]
    recent = Mod.query.filter(Mod.published).order_by(desc(Mod.updated)).limit(3)[:3]
    user_count = User.query.count()
    mod_count = Mod.query.count()
    yours = list()
    if current_user:
        yours = sorted(current_user.following, key=lambda m: m.updated, reverse=True)[:3]
    return render_template("index.html",\
        featured=featured,\
        new=new,\
        top=top,\
        recent=recent,\
        user_count=user_count,\
        mod_count=mod_count,
        yours=yours,
		site_name=_cfg('site-name'),
		support_mail=_cfg('support-mail'),
		source_code=_cfg('source-code'))

@anonymous.route("/browse")
def browse():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 6)[:6][0]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(6)[:6]
    return render_template("browse.html", featured=featured, top=top, new=new, site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/browse/new")
def browse_new():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.created))
    total_pages = math.ceil(mods.count() / 30)
    page = request.args.get('page')
    if page:
        page = int(page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
    else:
        page = 1
    mods = mods.offset(30 * (page - 1)).limit(30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/new", name="Newest Mods", rss="/browse/new.rss", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/browse/new.rss")
def browse_new_rss():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.created))
    mods = mods.limit(30)
    return Response(render_template("rss.xml", mods=mods, title="New mods on " + _cfg('site-name'),\
            description="The newest mods on " + _cfg('site-name'), \
            url="/browse/new", site_name=_cfg('site-name'), support_mail=_cfg('support-mail')), 
			mimetype="text/xml")

@anonymous.route("/browse/updated")
def browse_updated():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.updated))
    total_pages = math.ceil(mods.count() / 30)
    page = request.args.get('page')
    if page:
        page = int(page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
    else:
        page = 1
    mods = mods.offset(30 * (page - 1)).limit(30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/updated", name="Recently Updated Mods", rss="/browse/updated.rss", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/browse/updated.rss")
def browse_updated_rss():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.updated))
    mods = mods.limit(30)
    return Response(render_template("rss.xml", mods=mods, title="Recently updated on " + _cfg('site-name'),\
            description="Mods on " + _cfg('site-name') + " updated recently", \
            url="/browse/updated", site_name=_cfg('site-name'), support_mail=_cfg('support-mail')),
			mimetype="text/xml")

@anonymous.route("/browse/top")
def browse_top():
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 1
    mods, total_pages = search_mods("", page, 30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/top", name="Popular Mods", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/browse/featured")
def browse_featured():
    mods = Featured.query.order_by(desc(Featured.created))
    total_pages = math.ceil(mods.count() / 30)
    page = request.args.get('page')
    if page:
        page = int(page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
    else:
        page = 1
    if page != 0:
        mods = mods.offset(30 * (page - 1)).limit(30)
    mods = [f.mod for f in mods]
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/featured", name="Featured Mods", rss="/browse/featured.rss", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/browse/featured.rss")
def browse_featured_rss():
    mods = Featured.query.order_by(desc(Featured.created))
    mods = mods.limit(30)
    # Fix dates
    for f in mods:
        f.mod.created = f.created
    mods = [dumb_object(f.mod) for f in mods]
    db.rollback()
    return Response(render_template("rss.xml", mods=mods, title="Featured mods on " + _cfg('site-name'),\
            description="Featured mods on " + _cfg('site-name'), \
            url="/browse/featured", site_name=_cfg('site-name'), support_mail=_cfg('support-mail')), 
			mimetype="text/xml")

@anonymous.route("/about")
def about():
    return render_template("about.html", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/markdown")
def markdown_info():
    return render_template("markdown.html", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/privacy")
def privacy():
    return render_template("privacy.html", site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/search")
def search():
    query = request.args.get('query')
    if not query:
        query = ''
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 1
    mods, total_pages = search_mods(query, page, 30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages, search=True, query=query, site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))

@anonymous.route("/c/")
def c():
    s = r.get_subreddit("awwnime").get_hot(limit=212)
    return render_template("c.html", s=s, site_name=_cfg('site-name'), support_mail=_cfg('support-mail'))
