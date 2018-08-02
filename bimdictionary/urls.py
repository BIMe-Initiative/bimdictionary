from django.conf.urls import url
from django.conf.urls import include
from django.contrib import admin
from django.conf import settings


urlpatterns = [
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),

    # API urls
    url(
        r'^api/v1/dictionary/',
        include('dictionary.api.v1.urls', namespace='api')),

    # Dictionary
    url(r'^', include('dictionary.urls')),
    url(r'^froala_editor/', include('froala_editor.urls')),

]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
