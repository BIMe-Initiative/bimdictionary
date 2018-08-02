from django.core import mail

import pytest

from ..models import Term
from ..models import TermVersion
from ..models import TermContent


@pytest.mark.django_db
def test_term():
    term = Term.objects.create(
        title='Test Term',
        acronym='ABC',
        status=Term.PUBLISHED)

    assert term.slug == 'test-term'
    assert str(term) == 'Test Term (ABC)'


@pytest.mark.django_db
def test_termversion(userprofile):

    term = Term.objects.create(
        title='Test Term',
        status=Term.PUBLISHED)

    version = TermVersion.objects.create(term=term)
    term.current_version = version

    TermContent.objects.create(
        version=version,
        title=term.title,
        description='',
        author=userprofile)

    assert version.number == 1
    assert str(version) == 'Test Term 1'
    assert not version.other_versions.exists()
    assert version.is_current

    term.create_new_version()
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_termcontent(userprofile):
    term = Term.objects.create(
        title='Test Term',
        status=Term.PUBLISHED)
    version = TermVersion.objects.create(term=term)
    term.current_version = version

    description_fr = '''Suzanne et Joseph étaient nés dans les deux
    premières années de leur arrivée à la colonie. Après la naissance
    de Suzanne, la mère abandonna l’enseignement d’état.'''

    content_fr = TermContent.objects.create(
        version=version,
        title='Le Test Term',
        description=description_fr,
        language='fr')

    assert str(content_fr) == 'Le Test Term'
    assert not content_fr.is_rtl

    description_ar = '''استخدام النموذج يمثل كيف يتم توليد تفاصيل ثلاثية الأبعاد
    من النماذج ثلاثية الأبعاد الغنية بالمعلومات. تفاصيل ثلاثية الأبعاد عادة ما
    تشمل هجين من اللوحات التوضيحية ثنائية وثلاثية الأبعاد'''
    content_ar = TermContent.objects.create(
        version=version,
        title='تفصيل ثلاثي الأبعاد',
        description=description_ar,
        language='ar')

    assert str(content_ar) == 'تفصيل ثلاثي الأبعاد'
    assert content_ar.is_rtl

    assert content_ar in content_fr.other_languages
    assert content_fr in content_ar.other_languages


