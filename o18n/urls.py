import re

from django.urls import get_resolver

from django.utils import lru_cache
from django_extensions.management.commands.show_urls import RegexURLResolver

from . import monkey
from .util import get_country_language_prefix


def o18n_patterns(*urls, **kwargs):
    """
    Variant of django.conf.urls.i18n.i18_patterns.
    """
    prefix_default_country = kwargs.pop('prefix_default_country', True)
    return [CountryLanguageURLResolver(list(urls), prefix_default_country=prefix_default_country)]


@lru_cache.lru_cache(maxsize=None)
def is_country_prefix_patterns_used(urlconf):
    """
    Return a tuple of two booleans: (
        `True` if LocaleRegexURLResolver` is used in the `urlconf`,
        `True` if the default language should be prefixed
    )
    """
    for url_pattern in get_resolver(urlconf).url_patterns:
        if isinstance(url_pattern, CountryLanguageURLResolver):
            return True, url_pattern.prefix_default_country
    return False, False


class CountryLanguageURLResolver(RegexURLResolver):
    """
    Variant of django.core.urlresolvers.LocaleRegexURLResolver.
    """
    def __init__(self, urlconf_name, default_kwargs=None,
                 app_name=None, namespace=None, prefix_default_country=True):
        monkey.patch()          # Latest possible point for monkey patching.
        super(CountryLanguageURLResolver, self).__init__(
            None, urlconf_name, default_kwargs, app_name, namespace)
        self.prefix_default_country = prefix_default_country

    @property
    def regex(self):
        country_code = get_country_language_prefix()
        if country_code not in self._regex_dict:
            if country_code is None and not self.prefix_default_country:  # Regex that cannot be matched (hack).
                regex_string = ''
            else:
                regex_string = '^%s/' % country_code
            self._regex_dict[country_code] = re.compile(regex_string, re.UNICODE)
        return self._regex_dict[country_code]
