from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

def converter_para_webp(image_field, quality=80):
    """
    Lógica universal para converter qualquer ImageField para WebP.
    """
    if image_field and hasattr(image_field, 'file'):
        img = Image.open(image_field)
        
        if img.format != 'WEBP':
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            output = BytesIO()
            img.save(output, format='WEBP', quality=quality)
            output.seek(0)
            
            name = os.path.splitext(image_field.name)[0]
            new_filename = f"{name}.webp"
            
            # Retorna o arquivo pronto para ser salvo
            return ContentFile(output.read()), new_filename
    return None, None