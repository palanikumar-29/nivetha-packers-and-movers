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
    VEHICLE = 'vehicle', 'Vehicle Move'
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
    caption = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Gallery image'
        verbose_name_plural = 'Gallery'
        ordering = ['order', 'id']

    def __str__(self):
        return self.caption

