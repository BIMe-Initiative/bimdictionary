from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchRank
from django.contrib.postgres.search import SearchVector
from django.db.models import Q, F

from rest_framework import generics

from dictionary import models
from dictionary.api.v1 import serializers


class ConceptListView(generics.ListAPIView):
    serializer_class = serializers.ConceptSerializer
    permission_classes = []
    pagination_class = None

    def get_queryset(self):
        return models.Concept.objects.order_by('title')


class SimpleTermContentListView(generics.ListAPIView):

    permission_classes = []
    serializer_class = serializers.SimpleTermContentSerializer

    def get_queryset(self):
        q = self.request.GET.get('q')
        language = self.request.GET.get('language', 'en')

        qs = models.TermContent.objects.filter(
            is_latest=True, language=language)

        if q:
            qs = qs.filter(description__search=q)

        return qs.distinct()


class TermListView(generics.ListAPIView):

    permission_classes = []
    serializer_class = serializers.TermSerializer

    def get_queryset(self):
        q = self.request.GET.get('q')
        language = self.request.GET.get('language')
        country = self.request.GET.get('country')
        title = self.request.GET.get('title')
        concept = self.request.GET.get('concept')

        # Current versions
        qs = models.Term.objects.select_related(
            'current_version'
        ).prefetch_related(
            'versions',
            'versions__content',
            'concepts'
        ).filter(
            status=models.Term.PUBLISHED,
        ).order_by('title')

        if language:
            qs = qs.filter(
                Q(versions__content__language=language)
            )

        if title:
            return qs.filter(
                Q(versions__content__title__iexact=title) |
                Q(versions__term__pluraltitle__plural_title__iexact=title)
            ).distinct()

        if country:
            qs = qs.filter(country__iexact=country)

        if concept:
            qs = qs.filter(concepts__title__iexact=concept)

        if q:
            # Check for acronym match
            acronym_matches = qs.filter(versions__content__acronym__iexact=q)
            if acronym_matches.exists():
                return acronym_matches

            # Check for exact match
            exact_matches = qs.filter(title__iexact=q)
            if exact_matches.exists():
                return exact_matches

            # Full text search
            vector = SearchVector('title', weight='A') + \
                SearchVector('similar__title', weight='B') + \
                SearchVector('versions__content__description', weight='C')
            query = SearchQuery(q)
            qs = qs.annotate(
                rank=SearchRank(vector, query)
            ).filter(
                rank__gte=0.1
            ).order_by(
                'rank'
            )

        return qs.distinct()

