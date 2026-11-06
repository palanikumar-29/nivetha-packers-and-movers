from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from .models import Service, GalleryImage
from .forms import QuoteForm
from .channels import dispatch


def home(request):
    """
    Home page view displaying hero, road-sign route board, services summary,
    how a move works steps, and the quote request form.
    """
    submitted = request.GET.get('submitted') == '1'
    services_list = Service.objects.filter(is_active=True).order_by('order', 'id')

    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            is_spam = bool(form.cleaned_data.get('website'))
            if not is_spam:
                enquiry = form.save()
                dispatch(enquiry)
            return redirect(f"{reverse('core:home')}?submitted=1#quote-form")
    else:
        form = QuoteForm()

    return render(request, 'home.html', {
        'services': services_list,
        'form': form,
        'submitted': submitted,
    })


def services(request):
    """
    Services page view displaying all active services in order as a ruled list,
    with an empty state fallback and quote CTA.
    """
    services_list = Service.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'services.html', {
        'services': services_list,
    })


def gallery(request):
    """
    Gallery page view displaying active gallery images with lazy loading,
    image captions as alt text, and an empty state fallback.
    """
    images = GalleryImage.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'gallery.html', {
        'images': images,
    })


def about(request):
    """
    About page view with neutral, verifiable details about the business.
    """
    return render(request, 'about.html')


def contact(request):
    """
    Contact page view with phone, WhatsApp, address, and quote form submission handler.
    """
    submitted = request.GET.get('submitted') == '1'

    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            is_spam = bool(form.cleaned_data.get('website'))
            if not is_spam:
                enquiry = form.save()
                dispatch(enquiry)
            return redirect(f"{reverse('core:contact')}?submitted=1#quote-form")
    else:
        form = QuoteForm()

    return render(request, 'contact.html', {
        'form': form,
        'submitted': submitted,
    })


def robots_txt(request):
    """
    Serve robots.txt dynamically with Allow all, Disallow admin path, and Sitemap URL.
    """
    admin_url = (getattr(settings, 'ADMIN_URL', 'panel') or 'panel').strip('/') or 'panel'
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    content = f"User-agent: *\nAllow: /\nDisallow: /{admin_url}/\nSitemap: {site_url}/sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain")

