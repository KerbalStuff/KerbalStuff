from PIL import Image

def create(imagePath, thumbnailPath):
    im = Image.open(imagePath)
    im.thumbnail((320, 320), Image.ANTIALIAS)
    im.save(thumbnailPath)
