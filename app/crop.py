from PIL import Image


class Crop:

    @staticmethod
    def crop_image(img, coords, save):
        image = Image.open(img)
        cropped_image = image.crop(coords)
        cropped_image.save(save)
