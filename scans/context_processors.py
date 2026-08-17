from django.conf import settings


def version(request):
    """Expose the deployed commit so the footer can show which version is live."""
    return {"GIT_COMMIT_SHA": settings.GIT_COMMIT_SHA}
