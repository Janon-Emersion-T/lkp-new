from pathlib import Path

from django.core.exceptions import ValidationError


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_IMAGE_SIZE = 20 * 1024 * 1024


def validate_image_upload(value):
    if not value:
        return
    name = getattr(value, 'name', str(value))
    suffix = Path(name).suffix.lower()
    if suffix and suffix not in IMAGE_EXTENSIONS:
        raise ValidationError('Upload a JPG, PNG, or WebP image.')
    size = getattr(value, 'size', None)
    if size and size > MAX_IMAGE_SIZE:
        raise ValidationError('Image must be no larger than 20 MB.')
