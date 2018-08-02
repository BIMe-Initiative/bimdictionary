from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django_countries import countries
from froala_editor.widgets import FroalaEditor

from . import models

countries = [(None, '----------')] + list(countries)


class TermVersionForm(forms.Form):
    create_new_version = forms.BooleanField(required=False)
    make_current = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit('make_current', 'Make Current'),
            Submit('create_new_version', 'Create New Version'),
        )


class TermForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            #'acronym',
            'country',
            'concepts',
            Submit('submit', 'Save'),
        )

    class Meta:
        model = models.Term
        fields = ['title', 'country', 'concepts']


class TermContentForm(forms.ModelForm):

    extended_description = forms.CharField(widget=FroalaEditor, required=False)
    similar_terms = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}), required=False)
    plural_titles = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'plural_titles',
            'acronym',
            'description',
            'extended_description',
            'similar_terms',
            Submit('submit', 'Submit')
        )

    class Meta:
        model = models.TermContent
        fields = ['title', 'acronym', 'description', 'extended_description']

    def clean_similar_terms(self):
        similar = self.cleaned_data['similar_terms']
        return {x.strip() for x in similar.splitlines() if x.strip()}

    def clean_plural_titles(self):
        plurals = self.cleaned_data['plural_titles']
        return {x.strip() for x in plurals.splitlines() if x.strip()}

    def clean(self, *args, **kwargs):
        if not self.cleaned_data.get('title') and \
                not self.cleaned_data.get('description'):
            raise ValidationError(
                "Translation must have a title or description")

    def save(self, *args, **kwargs):
        instance = super().save(*args, *kwargs)
        self.save_synonyms(instance)
        self.save_plurals(instance)
        return instance

    def save_plurals(self, instance):

        existing_plurals = set(
            instance.plurals.values_list('plural_title', flat=True)
        )
        new_plurals = self.cleaned_data['plural_titles']

        # Delete existing plurals not in new plurals
        to_delete = existing_plurals.difference(new_plurals)
        models.PluralTitle.objects.filter(
            language=instance.language,
            plural_title__in=to_delete
        ).delete()

        # Create new plurals
        if new_plurals:
            for plural in new_plurals:
                models.PluralTitle.objects.get_or_create(
                    term=instance.version.term,
                    language=instance.language,
                    plural_title=plural,
                )

    def save_synonyms(self, instance):

        existing_similar = set(
            instance.similar.values_list('title', flat=True)
        )
        new_similar = self.cleaned_data['similar_terms']

        # Delete existing similar not in new similar
        to_delete = existing_similar.difference(new_similar)
        models.Synonym.objects.filter(
            language=instance.language,
            title__in=to_delete
        ).delete()

        # Create new synonyms
        if new_similar:
            for similar in new_similar:
                models.Synonym.objects.get_or_create(
                    canonical_term=instance.version.term,
                    language=instance.language,
                    title=similar,
                )


