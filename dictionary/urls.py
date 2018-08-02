from django.conf.urls import url
from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView


from dictionary import views


urlpatterns = [

    path(
        'term-autocomplete/',
        views.TermAutocomplete.as_view(),
        name='term-autocomplete'),

    path(
        'termversion-autocomplete/',
        views.TermVersionAutocomplete.as_view(),
        name='termversion-autocomplete'),

    path(r'embed/', views.embed_view, name='embed'),
    path(
        'embed-test/',
        TemplateView.as_view(template_name='dictionary/embed_test.html'),
        name='embed-test'),

    url(r'^manage/$', views.ManageView.as_view(), name='manage'),

    url(r'^$',
        cache_page(360)(views.DictionaryIndexView.as_view(
            template_name='dictionary/index.html')),
        name='index'),
    url(r'^(?P<language>[a-z]{2})/(?P<slug>[-a-zA-Z0-9]+)/(?P<version>\d+)/$',
        cache_page(360)(views.TermDetailView.as_view(
            template_name='dictionary/term_detail.html')),
        name='term-detail'),

    url(r'^(?P<language>[a-z]{2})/(?P<slug>[-a-zA-Z0-9]+)/$',
        views.TermDetailRedirectView.as_view(), name='term-detail-redirect-a'),
    url(r'^(?P<slug>[-a-zA-Z0-9]+)/$',
        views.TermDetailRedirectView.as_view(), name='term-detail-redirect-b'),

    path(
        '<int:term_id>.<int:version>.<slug:language>/',
        views.TermDetailRedirectView.as_view(), name='term-detail-redirect-code'),

    url(
        r'^manage/(?P<slug>[-a-zA-Z0-9]+)/(?P<version>\d+)/$',
        views.TermManageView.as_view(),
        name='term-manage'),

    url(
        r'^manage/(?P<slug>[-a-zA-Z0-9]+)/$',
        views.TermUpdateView.as_view(),
        name='term-edit'),

    url(
        r'^manage/(?P<slug>[-a-zA-Z0-9]+)/version/new/$',
        views.TermVersionCreateView.as_view(),
        name='term-version-add'),

    url(
        r'^manage/(?P<language>[a-z]{2})/(?P<slug>[-a-zA-Z0-9]+)/(?P<version>\d+)/edit/$',
        views.TermContentUpdateView.as_view(),
        name='term-content-edit'),

    url(
        r'^manage/(?P<language>[a-z]{2})/(?P<slug>[-a-zA-Z0-9]+)/(?P<version>\d+)/add/$',
        views.TermContentCreateView.as_view(),
        name='term-content-add'),
]

