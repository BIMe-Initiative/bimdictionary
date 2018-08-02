import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.decorators.clickjacking import xframe_options_exempt

from django_countries import countries
from dal import autocomplete

from core.languages import LANGUAGES
from . import forms
from . import models


all_languages = dict(LANGUAGES)
all_countries = dict(countries)


class TermAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = models.Term.objects.all()
        if self.q:
            qs = qs.filter(title__istartswith=self.q)

        return qs


class TermVersionAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = models.TermVersion.objects.all()
        if self.q:
            qs = qs.filter(term__title__istartswith=self.q)

        return qs


@xframe_options_exempt
def embed_view(request):
    context = {
        'language': request.GET.get('language', 'en')
    }
    return render(request, 'dictionary/embed.html', context)


class DictionaryIndexView(TemplateView):
    template_name = 'dictionary/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        used_countries = set(x.upper() for x in
            models.Term.objects.values_list('country', flat=True) if x)
        country_codes = []
        for country in used_countries:
            country_codes.append(
                {'code': country, 'name': all_countries.get(country)})
        context['country_codes'] = json.dumps(country_codes)
        languages = []
        used_languages = sorted(list(set(
            models.TermContent.objects.values_list('language', flat=True))))
        for language in used_languages:
            languages.append({
                'code': language,
                'name': str(all_languages.get(language))})
        context['languages'] = json.dumps(languages)
        return context


class TermDetailView(DetailView):
    model = models.TermContent
    template_name = 'dictionary/term_detail.html'

    def get_object(self, queryset=None, *args, **kwargs):
        term_content = get_object_or_404(
            models.TermContent,
            version__number=self.kwargs['version'],
            version__term__slug=self.kwargs['slug'].lower(),
            language=self.kwargs['language']
        )
        return term_content

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        termcontent = self.get_object()
        context['version'] = termcontent.version
        context['term'] = termcontent.version.term
        return context


class TermDetailRedirectView(RedirectView):
    permanent = True
    pattern_name = 'term-detail'

    def get_redirect_url(self, *args, **kwargs):
        if 'language' in kwargs:
            language = kwargs['language']
        else:
            language = 'en'

        if 'term_id' in kwargs:
            term = get_object_or_404(
                models.Term,
                id=kwargs['term_id'])
        else:
            term = get_object_or_404(
                models.Term,
                slug=kwargs['slug'].lower())
        if 'version' in kwargs:
            term_version = get_object_or_404(
                models.TermVersion,
                term=term,
                number=kwargs['version'],
            )
        else:
            term_version = term.current_version

        return reverse(
            'term-detail',
            args=[language, term.slug, term_version.number]
        )


# Manage views


class TermManageView(PermissionRequiredMixin, FormView):
    form_class = forms.TermVersionForm
    template_name = 'dictionary/term_manage.html'
    permission_required = [
        'dictionary.change_termcontent',
        'dictionary.add_termcontent']

    def get_object(self, queryset=None, *args, **kwargs):
        termversion = get_object_or_404(
            models.TermVersion,
            number=self.kwargs['version'],
            term__slug=self.kwargs['slug'].lower(),
        )
        return termversion

    def form_valid(self, form):
        term_version = self.get_object()
        term = term_version.term
        url = reverse(
            'term-manage',
            args=[term.slug, term_version.number])
        if form.cleaned_data.get('make_current'):
            term.set_current(term_version)
        if form.cleaned_data.get('create_new_version'):
            new_version = term.create_new_version()
            url = reverse(
                'term-manage',
                args=[term.slug, new_version.number])
        return HttpResponseRedirect(url)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        termversion = self.get_object()
        term = termversion.term

        context['termversion'] = termversion
        context['term'] = term
        context['languages'] = termversion.language_map

        return context


class TermUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.Term
    form_class = forms.TermForm
    permission_required = 'dictionary.change_term'

    def get_success_url(self):
        term = self.get_object()
        return reverse('term-manage', args=[term.slug, term.version_number])


class TermVersionCreateView(PermissionRequiredMixin, View):

    permission_required = 'dictionary.add_termversion'

    def get(self, *args, **kwargs):
        term = get_object_or_404(models.Term, slug=kwargs['slug'])
        new_version = term.create_new_version()

        return HttpResponseRedirect(
            reverse('term-manage', args=[term.slug, new_version.number])
        )


class TermContentUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.TermContent
    form_class = forms.TermContentForm
    permission_required = 'dictionary.change_termcontent'

    def get_initial(self):
        obj = self.get_object()
        similar = obj.similar.values_list('title', flat=True)
        plurals = obj.plurals.values_list('plural_title', flat=True)
        return {
            'similar_terms': '\n'.join(similar),
            'plural_titles': '\n'.join(plurals),
        }

    def get_object(self, queryset=None, *args, **kwargs):
        term_content = get_object_or_404(
            models.TermContent,
            version__number=self.kwargs['version'],
            version__term__slug=self.kwargs['slug'].lower(),
            language=self.kwargs['language']
        )
        return term_content

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['version'] = self.get_object().version
        context['language'] = self.get_object().language
        return context

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url

        term_content = self.get_object()
        term_version = term_content.version
        term = term_version.term
        return reverse('term-manage', args=[term.slug, term.version_number])


class TermContentCreateView(PermissionRequiredMixin, CreateView):
    model = models.TermContent
    form_class = forms.TermContentForm
    permission_required = 'dictionary.add_termcontent'

    def get_initial(self):
        term = models.Term.objects.get(slug=self.kwargs['slug'])
        last_content = term.get_last_content(self.kwargs['language'])
        if last_content:
            return {
                'title': last_content.title,
                'description': last_content.description,
                'extended_description': last_content.extended_description,
                'acronym': last_content.acronym,
                'plural_titles': '\n'.join(
                    last_content.plurals.values_list('plural_title', flat=True)
                ),
                'similar_terms': '\n'.join(
                    last_content.similar.values_list('title', flat=True)
                ),
            }

    def get(self, request, *args, **kwargs):
        term = models.Term.objects.get(slug=kwargs['slug'])
        existing = models.TermContent.objects.filter(
            version__term=term,
            version__number=kwargs['version'],
            language=kwargs['language'])
        if existing.exists():
            messages.warning(
                request, '{} already exists'.format(existing.first()))
            url = reverse(
                'term-content-edit',
                args=[kwargs['language'], kwargs['slug'], kwargs['version']])
            return HttpResponseRedirect(url)

        return super().get(request, *args, **kwargs)

    def get_version(self):
        term = models.Term.objects.get(slug=self.kwargs['slug'])
        version = models.TermVersion.objects.get(
            term=term, number=self.kwargs['version'])
        return version

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['version'] = self.get_version()
        context['language'] = all_languages.get(self.kwargs['language'])
        return context

    def form_valid(self, form):
        version = self.get_version()
        content = models.TermContent.objects.create(
            language=self.kwargs['language'],
            version=version,
            title=form.cleaned_data['title'],
            description=form.cleaned_data['description'],
        )
        messages.info(
            self.request,
            '{} translation added'.format(content.get_language_display()))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'term-manage', args=[self.kwargs['slug'], self.kwargs['version']])


class ManageView(PermissionRequiredMixin, ListView):
    template_name = 'dictionary/manage.html'
    paginate_by = 20
    permission_required = [
        'dictionary.add_termcontent',
        'dictionary.change_termcontent',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        q = self.request.GET.get('q', '')
        language = self.request.GET.get('language')

        if q:
            context['extra_params'] = 'q={}'.format(q)

        context['q'] = q
        context['language'] = language
        context['languages'] = LANGUAGES

        return context

    def get_queryset(self):
        qs = models.Term.objects.order_by('title')
        q = self.request.GET.get('q')

        if q:
            qs = qs.filter(title__icontains=q)

        return qs

