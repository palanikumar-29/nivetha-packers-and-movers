import urllib.parse
from django.contrib import admin
from django.utils.html import format_html
from .models import QuoteRequest, EnquiryStatus, Service, GalleryImage
from .forms import GalleryImageAdminForm


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'move_type',
        'moving_from',
        'moving_to',
        'status_badge',
        'created_at',
    )
    list_filter = ('status', 'move_type', 'created_at')
    search_fields = ('name', 'phone', 'moving_from', 'moving_to')
    readonly_fields = ('whatsapp_link', 'created_at', 'status_updated_at')

    fieldsets = (
        ('Enquiry Details', {
            'fields': (
                'name',
                'phone',
                'whatsapp_link',
                'move_type',
                'moving_from',
                'moving_to',
                'preferred_date',
                'details',
                'created_at',
            )
        }),
        ('Status & Notes', {
            'fields': (
                'status',
                'notes',
                'status_updated_at',
            )
        }),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        if obj.status == EnquiryStatus.NEW:
            return format_html(
                '<span class="badge-new amber-highlight" style="background-color: #f59e0b; color: #1c1917; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{}</span>',
                obj.get_status_display()
            )
        return obj.get_status_display()

    @admin.display(description='WhatsApp customer')
    def whatsapp_link(self, obj):
        if not obj or not obj.phone:
            return '-'
        phone = obj.phone.strip()
        name = obj.name.strip()
        move_type_name = obj.get_move_type_display() if hasattr(obj, 'get_move_type_display') else obj.move_type
        move_summary = f"{move_type_name} from {obj.moving_from} to {obj.moving_to}"
        text = f"Hello {name}, thank you for your enquiry with Nivetha Packers and Movers regarding {move_summary}."
        wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(text)}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer" class="button" '
            'style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; '
            'background-color: #25D366; color: #ffffff; border-radius: 4px; text-decoration: none; font-weight: 600;">'
            'WhatsApp customer</a>',
            wa_url
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = ['whatsapp_link', 'created_at', 'status_updated_at']
        is_super = bool(request and getattr(request, 'user', None) and request.user.is_superuser)
        if obj and not is_super:
            readonly.extend([
                'name',
                'phone',
                'move_type',
                'moving_from',
                'moving_to',
                'preferred_date',
                'details',
            ])
        return tuple(readonly)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    form = GalleryImageAdminForm
    list_display = ('caption', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('caption',)
