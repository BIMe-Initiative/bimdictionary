import pytest

from core.models import UserProfile


@pytest.fixture()
def userprofile(db):
    return UserProfile.objects.create_user(
        email='test@test.com', password='test')

