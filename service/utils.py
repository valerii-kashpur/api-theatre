import os
import uuid

from django.utils.text import slugify


def image_file_path(instance, filename, folder: str):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"

    return os.path.join(f"uploads/{folder}/", filename)
