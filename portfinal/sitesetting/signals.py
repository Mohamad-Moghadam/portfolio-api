import logging
import requests
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Post

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Post)
def revalidate_nextjs(sender, instance, **kwargs):
    """Tell Next.js to rebuild affected pages the moment content changes."""
    url = getattr(settings, "NEXTJS_REVALIDATE_URL", "")
    if not url:
        return
    try:
        requests.post(
            url,
            json={
                "secret": settings.NEXTJS_REVALIDATE_SECRET,
                "paths": ["/blog", f"/blog/{instance.slug}", "/"],
            },
            timeout=3,
        )
    except requests.RequestException:
        logger.warning("Next.js revalidation failed — ISR timer will catch it.")