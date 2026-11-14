from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r'^[6-9]\d{9}$',
    message='Phone number must be a 10-digit Indian mobile number starting with 6, 7, 8, or 9.'
)


class MoveType(models.TextChoices):
    HOUSE = 'house', 'House Move'
    OFFICE = 'office', 'Office Move'
    FACTORY = 'factory', 'Factory / Commercial'
    OTHER = 'other', 'Other'


class EnquiryStatus(models.TextChoices):
    NEW = 'New', 'New'
    CALLED = 'Called', 'Called'
    CONFIRMED = 'Confirmed', 'Confirmed'
    CLOSED = 'Closed', 'Closed'


class QuoteRequest(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    move_type = models.CharField(
        max_length=20,
        choices=MoveType.choices,
        default=MoveType.HOUSE
    )
    moving_from = models.CharField(max_length=100)
    moving_to = models.CharField(max_length=100)
    preferred_date = models.DateField(null=True, blank=True)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=EnquiryStatus.choices,
        default=EnquiryStatus.NEW
    )
    notes = models.TextField(blank=True, help_text='Internal notes for Client user only')
    created_at = models.DateTimeField(auto_now_add=True)
    status_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Enquiry'
        verbose_name_plural = 'Enquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.get_move_type_display()} ({self.status})"

    def save(self, *args, **kwargs):
        if self.pk:
            orig = QuoteRequest.objects.filter(pk=self.pk).values('status').first()
            if orig and orig['status'] != self.status:
                self.status_updated_at = timezone.now()
        super().save(*args, **kwargs)


class Service(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Gallery image'
        verbose_name_plural = 'Gallery'
        ordering = ['order', 'id']

    def __str__(self):
        return self.caption or f"Gallery image {self.pk or ''}"

    @property
    def optimized_url(self):
        """
        Return the image URL with automatic format, quality, and width limiting
        when hosted on Cloudinary, or raw URL for local storage.
        """
        if not self.image:
            return ''
        url = self.image.url
        if 'res.cloudinary.com' in url and '/upload/' in url:
            return url.replace('/upload/', '/upload/f_auto,q_auto,w_1600,c_limit/', 1)
        return url


PALETTES = [
    ('beige', 'Beige'),
    ('navy', 'Navy'),
]
PALETTE_NAMES = [p[0] for p in PALETTES]
DEFAULT_PALETTE = 'beige'


def get_default_palette():
    from django.conf import settings
    val = getattr(settings, 'SITE_PALETTE', DEFAULT_PALETTE)
    return val if val in PALETTE_NAMES else DEFAULT_PALETTE


class SiteSettings(models.Model):
    palette = models.CharField(
        max_length=20,
        choices=PALETTES,
        default=get_default_palette,
        help_text='Visual color theme preset for the website (beige or navy).'
    )
    logo = models.ImageField(
        upload_to='site/',
        blank=True,
        null=True,
        help_text='Optional site logo image. If empty, the header displays the text wordmark.'
    )

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return f"Site settings ({self.get_palette_display()})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.set('site_palette', self.palette, timeout=300)
        if self.logo:
            cache.set('site_logo_url', self.logo.url, timeout=300)
        else:
            cache.delete('site_logo_url')

    def delete(self, *args, **kwargs):
        # Prevent deleting the singleton settings row
        pass

    @classmethod
    def get_solo(cls):
        from django.core.cache import cache
        from django.conf import settings

        cached = cache.get('site_palette')
        if cached and cached in PALETTE_NAMES:
            return cached

        default_env = getattr(settings, 'SITE_PALETTE', DEFAULT_PALETTE)
        if default_env not in PALETTE_NAMES:
            default_env = DEFAULT_PALETTE

        try:
            obj = cls.objects.first()
            if not obj:
                obj = cls.objects.create(pk=1, palette=default_env)
            palette = obj.palette if obj.palette in PALETTE_NAMES else default_env
        except Exception:
            palette = default_env

        cache.set('site_palette', palette, timeout=300)
        return palette

    @classmethod
    def get_logo_url(cls):
        from django.core.cache import cache
        from django.conf import settings
        from django.templatetags.static import static

        cached = cache.get('site_logo_url')
        if cached:
            return cached

        logo_url = ''
        try:
            obj = cls.objects.first()
            if obj and obj.logo:
                logo_url = obj.logo.url
        except Exception:
            pass

        if not logo_url:
            static_logo = getattr(settings, 'SITE_LOGO', '')
            if static_logo:
                try:
                    logo_url = static(static_logo)
                except Exception:
                    static_url = getattr(settings, 'STATIC_URL', '/static/')
                    logo_url = f"{static_url.rstrip('/')}/{static_logo.lstrip('/')}"

        if logo_url:
            cache.set('site_logo_url', logo_url, timeout=300)
        return logo_url


