from flask import Blueprint, render_template, abort, request, redirect, session, Response
from flask.ext.login import current_user
from sqlalchemy import desc
from KerbalStuff.objects import Featured, BlogPost, Mod, ModVersion, Publisher, Game
from KerbalStuff.search import search_mods
from KerbalStuff.common import *
from KerbalStuff.config import _cfg

import math

anonymous = Blueprint('anonymous', __name__, template_folder='../../templates/anonymous')

@anonymous.route("/")
def index():
    games = Game.query.filter(Game.active == True).order_by(desc(Game.created))
    return render_template("index.html",\
        games=games)

@anonymous.route("/<gameshort>")
def game(gameshort):

    ga = Game.query.filter(Game.short == gameshort).first()
    session['game'] = ga.id;
    session['gamename'] = ga.name;
    session['gameshort'] = ga.short;
    session['gameid'] = ga.id;
    featured = Featured.query.filter(Mod.game_id == ga.id).order_by(desc(Featured.created)).limit(6)[:6]
    #top = search_mods("", 1, 3)[0]
    top = Mod.query.filter(Mod.published,Mod.game_id == ga.id).order_by(desc(Mod.download_count)).limit(3)[:3]
    new = Mod.query.filter(Mod.published,Mod.game_id == ga.id).order_by(desc(Mod.created)).limit(3)[:3]
    recent = Mod.query.filter(Mod.published,Mod.game_id == ga.id, ModVersion.query.filter(ModVersion.mod_id == Mod.id).count() > 1).order_by(desc(Mod.updated)).limit(3)[:3]
    user_count = User.query.count()
    mod_count = Mod.query.count()
    yours = list()
    if current_user:
        yours = sorted(current_user.following, key=lambda m: m.updated, reverse=True)[:3]
    return render_template("game.html",\
        ga=ga,\
        featured=featured,\
        new=new,\
        top=top,\
        recent=recent,\
        user_count=user_count,\
        mod_count=mod_count,
        yours=yours)

@anonymous.route("/browse")
def browse():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 6)[:6][0]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(6)[:6]
    return render_template("browse.html", featured=featured, top=top, new=new)

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
            url="/browse/new", name="Newest Mods", rss="/browse/new.rss")

@anonymous.route("/browse/new.rss")
def browse_new_rss():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.created))
    mods = mods.limit(30)
    return Response(render_template("rss.xml", mods=mods, title="New mods on " + _cfg('site-name'),\
            description="The newest mods on " + _cfg('site-name'), \
            url="/browse/new"), mimetype="text/xml")

@anonymous.route("/browse/updated")
def browse_updated():
    mods = Mod.query.filter(Mod.published, ModVersion.query.filter(ModVersion.mod_id == Mod.id).count() > 1).order_by(desc(Mod.updated))
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
    mods = Mod.query.filter(Mod.published, ModVersion.query.filter(ModVersion.mod_id == Mod.id).count() > 1).order_by(desc(Mod.updated))
    mods = mods.limit(30)
    return Response(render_template("rss.xml", mods=mods, title="Recently updated on " + _cfg('site-name'),\
            description="Mods on " + _cfg('site-name') + " updated recently", \
            url="/browse/updated"), mimetype="text/xml")

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
            url="/browse/featured", name="Featured Mods", rss="/browse/featured.rss")

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
            url="/browse/featured"), mimetype="text/xml")

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
