import base64
from io import BytesIO
from PIL import Image
from config.dash_melon_conf import PathProj


class AvatarFile:
    @staticmethod
    def save_avatar_file(base64_str: str, img_type: str, user_name: str):
        file_like = BytesIO(base64.b64decode(base64_str))
        pil_img = Image.open(file_like)
        image_rgb = pil_img.convert('RGB')
        image_rgb = image_rgb.resize((256, 256))
        image_rgb.save(PathProj.AVATAR_DIR_PATH / f'{user_name}.jpg', quality=50)
