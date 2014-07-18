from KerbalStuff.database import db
from KerbalStuff.objects import ModVersion, Mod

for m in Mod.query.all():
    for i, v in enumerate(m.versions):
        print("Setting sort order " + str(i) + " on " + m.name + " " + v.friendly_version)
        v.sort_index = i
