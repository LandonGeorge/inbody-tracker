import pytest


@pytest.fixture(autouse=True)
def _media_root(settings, tmp_path):
    """Keep uploaded test files out of the real media directory."""
    settings.MEDIA_ROOT = tmp_path
