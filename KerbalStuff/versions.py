from KerbalStuff.objects import GameVersion

game_versions = list()

def load_versions():
    game_versions = [v for v in GameVersion.query.all()]
