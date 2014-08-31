from flask import Blueprint, render_template, abort, request, redirect, session
from sqlalchemy import desc
from KerbalStuff.objects import Featured, BlogPost, Mod
from KerbalStuff.search import search_mods
from KerbalStuff.common import *

import praw

anonymous = Blueprint('anonymous', __name__, template_folder='../../templates/anonymous')
r = praw.Reddit(user_agent="Kerbal Stuff")

@anonymous.route("/")
def index():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 6)[0]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(3)[:3]
    user_count = User.query.count()
    mod_count = Mod.query.count()
    return render_template("index.html",\
        featured=featured,\
        new=new,\
        top=top,\
        user_count=user_count,\
        mod_count=mod_count)

@anonymous.route("/browse")
def browse():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 6)[:6][0]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(6)[:6]
    return render_template("browse.html", featured=featured, top=top, new=new)

@anonymous.route("/browse/new")
def browse_new():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.created))
    total_pages = int(mods.count() / 30)
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
            url="/browse/new", name="Newest Mods")

@anonymous.route("/browse/top")
def browse_top():
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 1
    mods, total_pages = search_mods("", page, 30)
    total_pages = int(total_pages / 30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/top", name="Popular Mods")

@anonymous.route("/browse/featured")
def browse_featured():
    mods = Featured.query.order_by(desc(Featured.created))
    total_pages = int(mods.count() / 30)
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
            url="/browse/featured", name="Featured Mods")

@anonymous.route("/about")
def about():
    return render_template("about.html")

@anonymous.route("/markdown")
def markdown_info():
    return render_template("markdown.html")

@anonymous.route("/privacy")
def privacy():
    return render_template("privacy.html")

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
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages, search=True, query=query)

@anonymous.route("/c/")
def c():
    s = r.get_subreddit("awwnime").get_hot(limit=212)
    return render_template("c.html", s=s)
