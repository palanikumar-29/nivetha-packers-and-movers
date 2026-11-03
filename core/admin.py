from django.contrib import admin
from .models import QuoteRequest, Service, GalleryImage


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'move_type', 'moving_from', 'moving_to', 'status', 'created_at')
    list_filter = ('status', 'move_type', 'created_at')
    search_fields = ('name', 'phone', 'moving_from', 'moving_to')
    readonly_fields = ('created_at', 'status_updated_at')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('caption',)

