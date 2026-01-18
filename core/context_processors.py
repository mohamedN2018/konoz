from .models import SiteSettings, heroSection

def site_settings(request):
    return {
        "url_media": SiteSettings.objects.first()
    }

def heroSections(request):
    return {
        "hero_sections": heroSection.objects.first()
    }