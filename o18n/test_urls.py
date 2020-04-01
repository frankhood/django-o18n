from django.conf.urls import url

from .urls import o18n_patterns

from .test_views import info


urlpatterns = o18n_patterns(
    url(r'^$', info, name='default'),
    url(r'^subpath/$', info, name='subpath'),
) + [
    url(r'^xx/$', info),
    url(r'^yy/zz/$', info),
]
