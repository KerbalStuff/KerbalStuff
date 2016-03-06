from PIL import Image

def create(imagePath, thumbnailPath, thumbnailSize):
    im = Image.open(imagePath)
    im.thumbnail(thumbnailSize, Image.ANTIALIAS)
    im.save(thumbnailPath)
