from django.urls import path
from django.views.decorators.cache import cache_page

from dictionary.api.v1 import views

app_name = 'api'

urlpatterns = [
    path('simple/', views.SimpleTermContentListView.as_view()),
    path('concepts/', views.ConceptListView.as_view()),
    path(
        '',
        cache_page(60 * 60 * 12)(views.TermListView.as_view()),
        name='term-list'),
]
