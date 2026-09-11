from .models import SiteSettings


def site_settings(request):
    """Exposes SiteSettings to ALL templates via `{{ site_settings.logo.url }}` etc."""
    return {"site_settings": SiteSettings.load()}