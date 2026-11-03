from django.http import HttpResponse


def placeholder_home(request):
    """Placeholder view for Story 1.1 ensuring HTTP 200 response."""
    return HttpResponse(
        '<!DOCTYPE html>'
        '<html lang="en">'
        '<head>'
        '    <meta charset="UTF-8">'
        '    <title>Nivetha Packers and Movers</title>'
        '</head>'
        '<body style="font-family: sans-serif; background: #1e2124; color: #ffffff; padding: 2rem;">'
        '    <h1>Nivetha Packers and Movers</h1>'
        '    <p>Django project foundation and data models initialized successfully.</p>'
        '</body>'
        '</html>'
    )

