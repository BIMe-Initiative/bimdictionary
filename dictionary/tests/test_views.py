from django.urls import reverse
from django.contrib.auth.models import Permission

import pytest

from ..models import PluralTitle
from ..models import Synonym
from ..models import Term
from ..models import TermContent
from ..models import TermVersion
from core.models import UserProfile


@pytest.fixture()
def term(db):
    return Term.objects.create(title='Term1', status=Term.PUBLISHED)


@pytest.fixture()
def termversion(db, term):
    return TermVersion.objects.create(term=term)


@pytest.fixture()
def termcontent(db, termversion):
    return TermContent.objects.create(
        version=termversion,
        title='Term',
        description='',
        language='en')


@pytest.fixture()
def manage_userprofile(db):
    userprofile = UserProfile.objects.create_user(
        email='manage@test.com', password='manage')
    perms = [
        'add_termcontent',
        'change_termcontent',
        'add_term',
        'change_term',
        'add_termversion',
        'change_termversion',
    ]
    for perm in perms:
        userprofile.user_permissions.add(
            Permission.objects.get(codename=perm))
    return userprofile


@pytest.mark.django_db
def test_index(client):
    resp = client.get(reverse('index'))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_detail(client, termcontent, term):
    term.current_version = termcontent.version
    term.save()

    url = reverse(
        'term-detail', args=[
            termcontent.language,
            termcontent.version.term.slug,
            termcontent.version.number
        ])
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.context['object'] == termcontent
    assert resp.context['termcontent'] == termcontent
    assert resp.context['version'] == termcontent.version
    assert resp.context['term'] == term


@pytest.mark.django_db
def test_redirects(client, termcontent, term):
    term.current_version = termcontent.version
    term.save()

    dest_url = reverse(
        'term-detail', args=[
            termcontent.language,
            termcontent.version.term.slug,
            termcontent.version.number
        ])

    # Redirect a
    url = reverse(
        'term-detail-redirect-a', args=[
            termcontent.language,
            term.slug
        ])
    resp = client.get(url)
    assert resp['Location'] == dest_url

    # Redirect b
    url = reverse(
        'term-detail-redirect-b', args=[
            term.slug
        ])
    resp = client.get(url)
    assert resp['Location'] == dest_url

    # Redirect code
    url = reverse(
        'term-detail-redirect-code', args=[
            term.id,
            termcontent.version.number,
            termcontent.language
        ])
    resp = client.get(url)
    assert resp['Location'] == dest_url


@pytest.mark.django_db
def test_manage_index(client, userprofile, manage_userprofile):
    url = reverse('manage')

    # Disallow anonymous user
    resp = client.get(url)
    assert resp.status_code == 302

    # Disallow regular user
    client.login(email=userprofile.email, password='test')
    resp = client.get(url)
    assert resp.status_code == 302

    # User with permissions is allowed
    client.login(email=manage_userprofile.email, password='manage')
    resp = client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_term_manage(
        client, userprofile, manage_userprofile, term, termcontent):

    term.current_version = termcontent.version
    term.save()

    url = reverse(
        'term-manage', args=[
            term.slug,
            termcontent.version.number
        ])

    # Disallow anonymous user
    resp = client.get(url)
    assert resp.status_code == 302

    # Disallow regular user
    client.login(email=userprofile.email, password='test')
    resp = client.get(url)
    assert resp.status_code == 302

    # User with permissions is allowed
    client.login(email=manage_userprofile.email, password='manage')
    resp = client.get(url)
    assert resp.status_code == 200

    assert resp.context['termversion'] == termcontent.version
    assert resp.context['term'] == term
    assert resp.context['languages'] == termcontent.version.language_map


@pytest.mark.django_db
def test_term_update(
        client, userprofile, manage_userprofile, term, termcontent):

    term.current_version = termcontent.version
    term.save()

    url = reverse(
        'term-edit', args=[
            term.slug,
        ])

    # Disallow anonymous user
    resp = client.get(url)
    assert resp.status_code == 302

    # Disallow regular user
    client.login(email=userprofile.email, password='test')
    resp = client.get(url)
    assert resp.status_code == 302

    # User with permissions is allowed
    client.login(email=manage_userprofile.email, password='manage')
    resp = client.get(url)
    assert resp.status_code == 200

    # Change title
    assert term.title == 'Term1'
    resp = client.post(url, {
        'title': 'XXX'
    })
    term.refresh_from_db()
    assert term.title == 'XXX'


@pytest.mark.django_db
def test_termversion_create(
        client, userprofile, manage_userprofile, term, termcontent):

    term.current_version = termcontent.version
    term.save()

    url = reverse(
        'term-version-add', args=[
            term.slug,
        ])

    dest_url = reverse(
        'term-manage', args=[
            term.slug, termcontent.version.number + 1
        ])

    # Disallow anonymous user
    resp = client.get(url)
    assert resp.status_code == 302

    # Disallow regular user
    client.login(email=userprofile.email, password='test')
    resp = client.get(url)
    assert resp.status_code == 302

    # User with permissions is allowed
    client.login(email=manage_userprofile.email, password='manage')
    resp = client.get(url)
    assert resp['Location'] == dest_url


@pytest.mark.django_db
def test_termcontent_edit(
        client, userprofile, manage_userprofile, term, termcontent):

    term.current_version = termcontent.version
    term.save()

    url = reverse(
        'term-content-edit', args=[
            termcontent.language,
            term.slug,
            term.current_version.number,
        ])

    dest_url = reverse(
        'term-manage', args=[
            term.slug, termcontent.version.number
        ])

    # Disallow anonymous user
    resp = client.get(url)
    assert resp.status_code == 302

    # Disallow regular user
    client.login(email=userprofile.email, password='test')
    resp = client.get(url)
    assert resp.status_code == 302

    # User with permissions is allowed
    client.login(email=manage_userprofile.email, password='manage')
    resp = client.get(url)
    assert resp.status_code == 200

    assert resp.context['version'] == term.current_version
    assert resp.context['language'] == termcontent.language
    assert resp.context['object'] == termcontent
    assert resp.context['termcontent'] == termcontent

    # Submit form
    resp = client.post(url, {
        'title': 'XXX',
        'plural_titles': '''
            Plural1
            Plural2
            Plural3
        ''',
        'acronym': '123',
        'similar_terms': '''
            Synonym1
            Synonym2
            Synonym3
        '''
    })
    assert resp['Location'] == dest_url

    termcontent.refresh_from_db()
    assert termcontent.title == 'XXX'

    synonyms = Synonym.objects.filter(
        canonical_term=term, language=termcontent.language)
    assert synonyms.count() == 3

    plurals = PluralTitle.objects.filter(
        term=term, language=termcontent.language)
    assert plurals.count() == 3

    # Submit form with blank plurals and synonyms
    resp = client.post(url, {
        'title': 'XXX',
        'acronym': 'ABC',
        'plural_titles': '',
        'similar_terms': '',
    })
    synonyms = Synonym.objects.filter(
        canonical_term=term, language=termcontent.language)
    assert synonyms.count() == 0

    plurals = PluralTitle.objects.filter(
        term=term, language=termcontent.language)
    assert plurals.count() == 0


@pytest.mark.django_db
def test_termcontent_create(
        client, userprofile, manage_userprofile, term, termcontent):

    term.current_version = termcontent.version
    term.save()

    url = reverse(
        'term-content-add', args=[
            termcontent.language,
            term.slug,
            term.current_version.number,
        ])

    dest_url = reverse(
        'term-manage', args=[
            term.slug, termcontent.version.number
        ])

    # Disallow anonymous user
    resp = client.get(url)
    assert resp.status_code == 302

    # Disallow regular user
    client.login(email=userprofile.email, password='test')
    resp = client.get(url)
    assert resp.status_code == 302

    # User with permissions is allowed
    client.login(email=manage_userprofile.email, password='manage')
    resp = client.get(url)
    assert resp.status_code == 200

    resp = client.post(url, {
        'title': 'New TermContent',
        'language': 'de',
        'version': term.current_version.id,
    })
    assert resp.status_code == 200
    assert resp['Location'] == dest_url


