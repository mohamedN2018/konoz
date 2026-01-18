from .models import SiteSettings, heroSection
from django.db.models import Count, Q
from .models import Post, Comment, User
from django.utils import timezone
from datetime import timedelta

def site_settings(request):
    return {
        "url_media": SiteSettings.objects.first()
    }

def heroSections(request):
    return {
        "hero_sections": heroSection.objects.first()
    }
