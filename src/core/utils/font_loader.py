from PIL import ImageFont

class FontLoader:

    FONT_TYPES: set[str] = {
        "Arial.ttf",
        "Helvetica.ttc",
        "DejaVuSans-Bold.ttf",
    }

    @classmethod
    def load(cls, size: int) -> ImageFont.FreeTypeFont:
        for font_type in cls.FONT_TYPES:
            try:
                return ImageFont.truetype(font_type, size=size)
            except IOError:
                continue
        return ImageFont.load_default()