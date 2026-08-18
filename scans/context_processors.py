from django.conf import settings


def version(request):
    """Expose the release version and deployed commit so the footer can show which version is live."""
    return {
        "APP_VERSION": settings.APP_VERSION,
        "GIT_COMMIT_SHA": settings.GIT_COMMIT_SHA,
    }
