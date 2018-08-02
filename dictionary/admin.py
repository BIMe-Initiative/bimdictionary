from django import forms
from django.contrib import admin

from froala_editor.widgets import FroalaEditor
from dal import autocomplete

from . import models


# Forms

class TermContentAdminForm(forms.ModelForm):

    class Meta:
        model = models.TermContent
        widgets = {
            'extended_description': FroalaEditor(),
            'version': autocomplete.ModelSelect2(
                url='termversion-autocomplete'),
        }
        fields = [
            'title',
            'language',
            'version',
            'acronym',
            'description',
            'extended_description']


class TermAdminForm(forms.ModelForm):

    class Meta:
        model = models.Term
        widgets = {
            'current_version': autocomplete.ModelSelect2(
                url='termversion-autocomplete'),
        }
        fields = [
            'title',
            'status',
            'country',
            'concepts',
            'current_version']


class TermVersionAdminForm(forms.ModelForm):

    class Meta:
        model = models.TermVersion
        widgets = {
            'term': autocomplete.ModelSelect2(url='term-autocomplete'),
        }
        fields = ['term', 'number']


class PluralTitleAdminForm(forms.ModelForm):

    class Meta:
        model = models.PluralTitle
        widgets = {
            'term': autocomplete.ModelSelect2(url='term-autocomplete'),
        }
        fields = ['term', 'plural_title', 'language']


class SynonymAdminForm(forms.ModelForm):

    class Meta:
        model = models.Synonym
        widgets = {
            'canonical_term': autocomplete.ModelSelect2(
                url='term-autocomplete'),
        }
        fields = ['title', 'description', 'slug', 'canonical_term', 'language']



# Inlines

def make_published(modeladmin, request, queryset):
    queryset.update(status=models.Term.STATUS_PUBLISHED)
    make_published.short_description = "Publish"


def make_rejected(modeladmin, request, queryset):
    queryset.update(status=models.Term.STATUS_REJECTED)
    make_published.short_description = "Reject"


class PluralInlineAdmin(admin.TabularInline):
    model = models.PluralTitle
    exclude = ['pl']


class TermContentInlineAdmin(admin.TabularInline):
    model = models.TermContent
    exclude = ['extended_description', 'author']


@admin.register(models.Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'version_number', 'language_string']
    actions = [make_published, make_rejected]
    search_fields = ['slug']
    filter_horizontal = ['concepts']
    list_per_page = 30
    fields = [
        'title', 'status', 'country', 'concepts', 'current_version']
    form = TermAdminForm

    def language_string(self, obj):
        return ', '.join(obj.languages)
    language_string.short_description = 'languages'

    def language_string(self, obj):
        return ', '.join(obj.languages)
    language_string.short_description = 'languages'


@admin.register(models.TermVersion)
class TermVersionAdmin(admin.ModelAdmin):
    inlines = [TermContentInlineAdmin]
    search_fields = ['term__title']
    readonly_fields = ['number']
    form = TermVersionAdminForm


@admin.register(models.TermContent)
class TermContentAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ['__str__', 'language', 'acronym', 'is_latest']
    list_filter = ['language', 'version__number', 'is_latest']
    form = TermContentAdminForm


@admin.register(models.Synonym)
class SynonymAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'canonical_term', 'language']
    list_filter = ['language']
    form = SynonymAdminForm


@admin.register(models.Concept)
class ConceptAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PluralTitle)
class PluralTitleAdmin(admin.ModelAdmin):
    list_display = ['plural_title', 'term', 'language']
    list_filter = ['language']
    form = PluralTitleAdminForm


