import os
from io import BytesIO
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image


def converter_para_webp(
    image_field: Any, quality: int = 80
) -> tuple[ContentFile, str] | tuple[None, None]:
    """
    Converte qualquer ImageField do Django para o formato WebP.

    Suporta modos RGBA e P (com transparência) preservando o canal alpha,
    e qualquer outro modo convertido para RGB antes da compressão.

    Args:
        image_field (ImageFieldFile): Campo de imagem Django cujo arquivo
            será convertido. Deve possuir o atributo ``file`` (campo preenchido).
        quality (int, optional): Nível de qualidade da compressão WebP,
            de 1 (menor qualidade) a 100 (sem perda). Padrão: 80.

    Returns:
        tuple[ContentFile, str]: Par ``(conteúdo_webp, novo_nome)`` onde
            ``conteúdo_webp`` é um :class:`~django.core.files.base.ContentFile`
            pronto para salvar e ``novo_nome`` é o nome original com extensão
            substituída por ``.webp``.
        tuple[None, None]: Quando ``image_field`` está vazio, não possui o
            atributo ``file``, ou a imagem já está no formato WebP.
    """
    if not (image_field and hasattr(image_field, "file")):
        return None, None

    img: Image.Image = Image.open(image_field)

    # Imagem já em WebP: não reconverte.
    if img.format == "WEBP":
        return None, None

    # Imagens com canal alpha (RGBA) ou indexadas por paleta (P) precisam ser
    # convertidas para RGBA antes de salvar em WebP para preservar a
    # transparência. Todos os outros modos vão direto para RGB.
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    output = BytesIO()
    img.save(output, format="WEBP", quality=quality)
    output.seek(0)

    name = os.path.splitext(image_field.name)[0]
    # Retorna o arquivo pronto para ser salvo
    return ContentFile(output.read()), f"{name}.webp"
