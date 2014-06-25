from KerbalStuff.objects import Mod, ModVersion, User
from KerbalStuff.database import db
from KerbalStuff.config import _cfg
from sqlalchemy import or_, and_, desc

from datetime import datetime

def weigh_result(result):
    # Factors considered, * indicates important factors:
    # High followers and high downloads get bumped*
    # Mods with a long version history get bumped
    # Mods with lots of screenshots or videos get bumped
    # Mods with a short description get docked
    # Mods lose points the longer they go without updates*
    # Mods get points for supporting the latest KSP version
    # Mods get points for being open source
    # New mods are given a hefty bonus to avoid drowning among established mods
    score = result.follower_count * 10
    score += result.download_count
    score += len(result.versions) / 5
    score += len(result.media)
    if len(result.description) < 100:
        score -= 10
    if result.updated:
        delta = (datetime.now() - result.updated).days
        if delta > 100:
            delta = 100 # Don't penalize for oldness past a certain point
        score -= delta / 5
    if len(result.versions) > 0:
        if result.versions[0].ksp_version == _cfg("latest-ksp"):
            score += 50
    if result.source_link:
        score += 10
    if (result.created - datetime.now()).days < 30:
        score += 100
    return score

def search_mods(text, page):
    terms = text.split(' ')
    query = db.query(Mod).join(Mod.user)
    filters = list()
    for term in terms:
        filters.append(Mod.name.ilike('%' + term + '%'))
        filters.append(User.username.ilike('%' + term + '%'))
        filters.append(Mod.description.ilike('%' + term + '%'))
        filters.append(Mod.short_description.ilike('%' + term + '%'))
    query = query.filter(or_(*filters))
    query = query.filter(Mod.published == True)
    query = query.order_by(desc(Mod.follower_count)) # We'll do a more sophisticated narrowing down of this in a moment
    query = query.limit(100)
    results = sorted(query.all(), key=weigh_result, reverse=True)
    return results[page * 10:page * 10 + 10]
