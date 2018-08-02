import pytest
from django.urls import reverse

from ..models import Concept
from ..models import Term
from ..models import TermVersion
from ..models import TermContent


@pytest.mark.django_db
def test_term_list(client):

    concept1 = Concept.objects.create(title='Test Concept')

    term1 = Term.objects.create(
        title='Term 1',
        status=Term.PUBLISHED)
    term1.concepts.add(concept1)

    term2 = Term.objects.create(
        title='Term 2',
        status=Term.PUBLISHED,
        country='AU')

    version1 = TermVersion.objects.create(term=term1)
    version2 = TermVersion.objects.create(term=term2)

    term1.current_version = version1
    term1.save()
    term2.current_version = version2
    term2.save()

    TermContent.objects.create(
        version=version1,
        title='Term 1',
        description='',
        language='en')
    TermContent.objects.create(
        version=version1,
        title='Le Term 1',
        description='',
        language='fr')
    TermContent.objects.create(
        version=version2,
        title='Term 2',
        description='This is the description')

    resp = client.get(reverse('api:term-list'))
    assert resp.status_code == 200
    results = resp.data['results']
    assert len(results) == 2

    # Search by title
    resp = client.get(reverse('api:term-list') + '?title=Term 1')
    results = resp.data['results']
    assert len(results) == 1
    assert results[0]['id'] == version1.id

    # Search by language
    resp = client.get(reverse('api:term-list') + '?language=fr')
    results = resp.data['results']
    assert len(results) == 1
    assert results[0]['id'] == version1.id

    resp = client.get(reverse('api:term-list') + '?language=ar')
    results = resp.data['results']
    assert len(results) == 0

    # Search by country
    resp = client.get(reverse('api:term-list') + '?country=AU')
    results = resp.data['results']
    assert len(results) == 1
    assert results[0]['id'] == version2.id

    # Search by concept
    resp = client.get(reverse('api:term-list') + '?concept=test concept')
    results = resp.data['results']
    assert len(results) == 1
    assert results[0]['id'] == version1.id

    # Search by text
    resp = client.get(reverse('api:term-list') + '?q=description')
    results = resp.data['results']
    assert len(results) == 1
    assert results[0]['id'] == version2.id

    resp = client.get(reverse('api:term-list') + '?q=term')
    results = resp.data['results']
    assert len(results) == 2

    resp = client.get(reverse('api:term-list') + '?q=aardvark')
    results = resp.data['results']
    assert len(results) == 0
