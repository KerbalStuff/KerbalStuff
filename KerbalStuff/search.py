from KerbalStuff.objects import Mod, ModVersion
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
    score = result.follower_count * 10
    score += result.download_count
    score += len(result.versions) / 5
    score += len(result.media)
    if len(result.description) < 100:
        score -= 10
    if result.updated:
        delta = (result.updated - datetime.now()).days
        if delta > 100:
            delta = 100 # Don't penalize for oldness past a certain point
        score -= delta / 5
    if len(result.versions) > 0:
        if result.versions[0].ksp_version == _cfg("latest-ksp"):
            score += 50
    if result.source_link:
        score += 10
    return score

def search_mods(text, page):
    terms = text.split(' ')
    query = db.query(Mod)
    filters = list()
    for term in terms:
        filters.append(Mod.name.like('%' + term + '%'))
        filters.append(Mod.description.like('%' + term + '%'))
        filters.append(Mod.short_description.like('%' + term + '%'))
    query.filter(or_(*filters))
    query.order_by(desc(Mod.follower_count)) # We'll do a more sophisticated narrowing down of this in a moment
    query.limit(100)
    results = query.all()
    results = sorted(results, key=weigh_result)
    return results
