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
    top = search_mods("", 0)[:3]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(3)[:3]
    return render_template("index.html", featured=featured, new=new, top=top)

@anonymous.route("/browse")
def browse():
    featured = Featured.query.order_by(desc(Featured.created)).limit(9)[:9]
    top = search_mods("", 0)[:7]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(9)[:9]
    return render_template("browse.html", featured=featured, top=top, new=new)

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
    results = search_mods(query, 0)
    wrapped = list()
    for result in results:
        m = wrap_mod(result)
        if m:
            wrapped.append(m)
    return render_template("search.html", results=wrapped, query=query)

@anonymous.route("/c/")
def c():
    s = r.get_subreddit("awwnime").get_hot(limit=212)
    return render_template("c.html", s=s)
