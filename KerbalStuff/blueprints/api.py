from flask import Blueprint, render_template, abort, request, redirect, session
from sqlalchemy import desc
from KerbalStuff.search import search_mods
from KerbalStuff.objects import *
from KerbalStuff.common import *

api = Blueprint('api', __name__)

@api.route("/api/search")
@json_output
def search():
    query = request.args.get('query')
    if not query:
        query = ''
    results = list()
    for m in search_mods(query, 0):
        a = {
            "name": m.name,
            "id": m.id,
            "short_description": m.short_description,
            "downloads": m.download_count,
            "followers": m.follower_count,
            "author": m.user.username
        }
        versions = list()
        for v in m.versions:
            versions.append({
                "friendly_version": v.friendly_version,
                "ksp_version": v.ksp_version,
                "id": v.id,
                "download_path": v.download_path,
                "changelog": v.changelog
            })
        a['versions'] = versions
        results.append(a)
    return results
