import os
import uuid

from django.utils.text import slugify


def image_file_path(
        instance,
        filename,
        folder: str = "other",
        unique_key: str = None
):
    _, extension = os.path.splitext(filename)

    if unique_key:
        unique_value = getattr(instance, unique_key)
        filename = f"{slugify(unique_value)}-{uuid.uuid4()}{extension}"
    else:
        filename = f"{uuid.uuid4()}{extension}"

    return os.path.join(f"uploads/{folder}/", filename)
