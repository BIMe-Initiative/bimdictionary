import re
from collections import OrderedDict
import functools

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from django_countries.fields import CountryField

from core.fields import LanguageField
from core.languages import LANGUAGES
from core.models import UserProfile

TERM_PAT = '\[\[(.[^\]\]]*)\]\]'
RTL_LANGUAGES = ['ar', 'fa']


class Concept(models.Model):
    title = models.CharField(max_length=100)
    created = models.DateTimeField('Date Created', auto_now_add=True)
    modified = models.DateTimeField('Date Modified', auto_now=True)

    def __str__(self):
        return self.title


class Term(models.Model):
    """
    Represents a dictionary term
    """
    SUGGESTED = 0
    REVIEWED = 1
    PUBLISHED = 2
    ARCHIVED = 3
    REJECTED = 4
    STATUSES = [
        (SUGGESTED, 'Suggested'),
        (REVIEWED, 'Reviewed'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
        (REJECTED, 'Rejected')]

    title = models.CharField(
        max_length=255,
        null=True,
        blank=True)
    slug = models.SlugField(unique=True, max_length=100)
    url = models.URLField(blank=True, null=True)
    status = models.SmallIntegerField(default=2, choices=STATUSES)
    country = CountryField(
        null=True,
        blank=True,
        help_text=_('Is this Term specific to one Country?'))
    concepts = models.ManyToManyField('Concept', blank=True)
    current_version = models.OneToOneField(
        'TermVersion',
        related_name='current_for_term',
        null=True,
        on_delete=models.SET_NULL)

    class Meta:
        app_label = 'dictionary'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.slug

    def get_absolute_url(self):
        return reverse('term-detail', args=['en', self.slug])

    def create_new_version(self):
        """
        Create a new version for this term.
        Should only allow one version greater than the current one
        """
        max_version = self.current_version.number + 1
        new_version, created = TermVersion.objects.get_or_create(
            term=self,
            number=max_version,
        )
        self.notify_new_version(new_version)

        return new_version

    def notify_new_version(self, new_version):
        """Send email to all authors for this term"""
        subject = 'New version of {} created'.format(self)
        body = '''\
A new version of {} has been created. Please review your translation and update accordingly.
http://{}{}
        '''.format(
            self,
            Site.objects.get_current().domain,
            reverse('term-manage', args=[self.slug, new_version.number])
        )
        author_emails = [x for x in self.authors.values_list('email', flat=True) if x]
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, author_emails)

    @property
    def authors(self):
        return UserProfile.objects.filter(
            termcontent__version__term=self).distinct()

    @property
    def version_number(self):
        return self.current_version.number if self.current_version else None

    @property
    def languages(self):
        return TermContent.objects.select_related(
            'version__term'
        ).filter(
            version__term=self
        ).values_list(
            'language',
            flat=True
        )

    @property
    @functools.lru_cache(32)
    def latest_versions(self):
        """Return a dictionary mapping languages to latest version numbers"""
        language_max = TermContent.objects.filter(
            version__term=self
        ).values(
            'language'
        ).annotate(
            models.Max('version__number')
        )
        return {x['language']: x['version__number__max'] for x in language_max}

    @property
    def latest_content(self):
        """Return a list of the latest content objects for this term"""
        return TermContent.objects.filter(version__term=self, is_latest=True)

    def set_current(self, termversion):
        self.current_version = termversion
        termversion.draft = False
        termversion.content.update(placeholder=False)
        termversion.save()
        self.save()

    def get_last_content(self, language):
        """Return the most recent TermContent object for a given language"""
        return TermContent.objects.filter(
            version__term=self,
            language=language
        ).order_by(
            '-version__number'
        ).first()


class TermVersion(models.Model):
    """
    A version of a term
    """
    created = models.DateTimeField('Date Created', auto_now_add=True)
    modified = models.DateTimeField('Date Modified', auto_now=True)
    term = models.ForeignKey(
        'Term', related_name='versions', on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    draft = models.BooleanField(default=True)

    class Meta:
        unique_together = ['term', 'number']
        ordering = ['term', 'number']

    def save(self, *args, **kwargs):
        other_versions = TermVersion.objects.filter(term=self.term)
        if self.id:
            other_versions = other_versions.exclude(id=self.id)
        if other_versions.exists():
            max_num = other_versions.aggregate(
                max_num=models.Max('number'))['max_num']
            self.number = max_num + 1
        else:
            self.number = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.term, self.number)

    def get_absolute_url(self):
        return reverse('term-detail', args=['en', self.term.slug, self.number])

    @property
    def is_current(self):
        return self.term.current_version == self

    @property
    def other_versions(self):
        return self.term.versions.exclude(Q(id=self.id) | Q(draft=True))

    @property
    def earlier_versions(self):
        return self.other_versions.filter(number__lte=self.number)

    @property
    def language_map(self):
        languages = OrderedDict([((x, y), None) for x, y in LANGUAGES])
        for content in self.content.order_by('language'):
            languages[(content.language, content.get_language_display())] = content
        return languages

    @property
    def english_content(self):
        return self.content.filter(language='en').first()


class TermContent(models.Model):
    """
    The content of a term in a particular language
    """
    created = models.DateTimeField('Date Created', auto_now_add=True)
    modified = models.DateTimeField('Date Modified', auto_now=True)
    version = models.ForeignKey(
        'TermVersion', related_name='content', on_delete=models.CASCADE)
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True)
    language = LanguageField(default='en')
    description = models.TextField(null=True, blank=True)
    rendered_description = models.TextField(null=True, blank=True)
    extended_description = models.TextField(null=True, blank=True)
    author = models.ForeignKey(
        UserProfile, null=True, blank=True, on_delete=models.CASCADE)
    placeholder = models.BooleanField(default=False)
    acronym = models.CharField(max_length=20, null=True, blank=True)
    is_latest = models.BooleanField(default=False)

    class Meta:
        unique_together = ['version', 'language']
        verbose_name_plural = 'Term content'

    def save(self, *args, **kwargs):
        existing = TermContent.objects.filter(id=self.id).first()
        if existing and self.placeholder:
            changed = existing.description != self.description or \
                existing.extended_description == self.description
            if changed:
                self.placeholder = False

        # Populate is_latest
        latest_version = self.version.term.latest_versions.get(self.language)
        self.is_latest = latest_version == self.version.number

        # Set is_latest on other term content objects to false
        TermContent.objects.filter(
            version__term=self.version.term,
            language=self.language
        ).exclude(
            id=self.id
        ).update(
            is_latest=False
        )

        # Populate rendered_description
        self.rendered_description = render_term(self.description)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'term-detail',
            args=[self.language, self.version.term.slug, self.version.number])

    @property
    def other_languages(self):
        """
        Return term content objects for each language of the highest version
        number
        """
        language_max = TermContent.objects.filter(
            version__term=self.version.term
        ).values(
            'language'
        ).annotate(
            models.Max('version__number')
        )
        out = []
        for language in language_max:
            content = TermContent.objects.get(
                version__term=self.version.term,
                version__number=language['version__number__max'],
                language=language['language'])
            out.append(content)

        return out

    @property
    def is_rtl(self):
        return self.language in RTL_LANGUAGES

    @property
    def similar(self):
        return Synonym.objects.filter(
            canonical_term=self.version.term,
            language=self.language)

    @property
    def plurals(self):
        return PluralTitle.objects.filter(
            term=self.version.term,
            language=self.language)

    @property
    def code(self):
        version = self.version.number if not self.placeholder else self.version.number - 1
        return '{}.{}.{}'.format(
            self.version.term.id, version, self.language)

    @property
    def permalink(self):
        scheme = 'https' if settings.HTTPS else 'http'
        domain = Site.objects.get_current().domain
        path = reverse(
            'term-detail-redirect-code',
            args=[
                self.version.term.id,
                self.version.term.current_version.number,
                self.language])
        return '{}://{}{}'.format(scheme, domain, path)


class PluralTitle(models.Model):
    """
    A plural for a term, can be language specific
    """
    term = models.ForeignKey('Term', on_delete=models.CASCADE)
    plural_title = models.CharField(max_length=255)
    language = LanguageField(default='en')

    class Meta:
        unique_together = ['plural_title', 'language']

    def __str__(self):
        return self.plural_title


class Synonym(models.Model):
    """
    Another name for a Term, can be language specific
    """
    created = models.DateTimeField('Date Created', auto_now_add=True)
    modified = models.DateTimeField('Date Modified', auto_now=True)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField()
    canonical_term = models.ForeignKey(
        'Term', related_name='similar', on_delete=models.CASCADE)
    language = LanguageField(default='en')

    def __str__(self):
        return self.title


def sub_callback(group):
    term_title = group.groups()[0]
    terms = Term.objects.filter(
        status=Term.PUBLISHED
    ).filter(
        Q(title__iexact=term_title) |
        Q(pluraltitle__plural_title__iexact=term_title) |
        Q(current_version__content__title__iexact=term_title)
    )
    if terms.exists():
        return '<a class="term" tabindex="0" title="{0}">{0}</a>'.format(
            term_title)
    else:
        return term_title


def render_term(text):
    rendered = re.sub(
        TERM_PAT,
        sub_callback,
        str(text))
    rendered = rendered.replace(
        '<<your/an>>', 'your').replace('<<OrgScale>>', 'organization')

    return rendered

