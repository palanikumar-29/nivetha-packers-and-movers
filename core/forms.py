from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from .models import QuoteRequest, MoveType, GalleryImage, phone_validator


class QuoteForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'})
    )

    class Meta:
        model = QuoteRequest
        fields = [
            'name',
            'phone',
            'move_type',
            'moving_from',
            'moving_to',
            'preferred_date',
            'details',
        ]
        widgets = {
            'move_type': forms.Select(choices=MoveType.choices),
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        phone_validator(phone)
        return phone

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data.get('preferred_date')
        if preferred_date:
            today = timezone.localdate()
            if preferred_date < today:
                raise forms.ValidationError("Preferred move date must be today or a future date.")
        return preferred_date


def validate_gallery_image(image):
    """
    Validate that an uploaded image file:
    1. Does not exceed 5 MB (5,242,880 bytes).
    2. Is a real JPEG, PNG, or WebP image by inspecting its binary content via Pillow.
    """
    if not image:
        return image

    if not isinstance(image, UploadedFile):
        return image

    max_size = 5 * 1024 * 1024  # 5 MB
    if image.size > max_size:
        raise forms.ValidationError("Image file size must not exceed 5 MB.")

    from PIL import Image, UnidentifiedImageError
    pos = image.file.tell() if hasattr(image.file, 'tell') else 0
    image.file.seek(0)
    try:
        with Image.open(image.file) as img:
            img_format = img.format
    except (UnidentifiedImageError, OSError):
        image.file.seek(pos)
        raise forms.ValidationError("The uploaded file is not a valid JPEG, PNG, or WebP image.")
    image.file.seek(pos)

    if img_format not in {'JPEG', 'PNG', 'WEBP'}:
        raise forms.ValidationError(
            f"Unsupported image format: {img_format}. Only JPEG, PNG, and WebP images are allowed."
        )

    return image


class GalleryImageAdminForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = '__all__'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        return validate_gallery_image(image)


