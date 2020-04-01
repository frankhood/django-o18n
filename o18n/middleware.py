from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

from . import country as country_mod
from . import util
from .urls import is_country_prefix_patterns_used


class CountryLanguageMiddleware(MiddlewareMixin):
    """
    Variant of django.middleware.locale.LocaleMiddleware.

    Uses the /<country>/<language>/ format for URL prefixes.

    Sets request.COUNTRY and request.LANGUAGE.
    """
    response_redirect_class = HttpResponseRedirect
    
    def process_request(self, request):
        country, language, language_code = util.get_country_language(request)
        if country is None:
            # country_mod.deactivate()
            country_mod.activate(util.get_default_country())
        else:
            country_mod.activate(country)
        translation.activate(language_code)

        request.COUNTRY = country
        request.LANGUAGE = language
        request.LANGUAGE_CODE = language_code

    def process_response(self, request, response):
        country, language, language_code = util.get_country_language(request)
        language_from_path = translation.get_language_from_path(request.path_info)
        country_from_path = util.get_country_from_path(request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        country_patterns_used, prefixed_default_country = is_country_prefix_patterns_used(urlconf)

        if (response.status_code == 404 and not country_from_path and
                country_patterns_used and prefixed_default_country):
            # Maybe the language code is missing in the URL? Try adding the
            # language prefix and redirecting to that URL.
            country_path = '/%s%s' % (country or util.get_default_country(), request.path_info)
            path_valid = is_valid_path(country_path, urlconf)
            path_needs_slash = (
                not path_valid and (
                    settings.APPEND_SLASH and not country_path.endswith('/') and
                    is_valid_path('%s/' % country_path, urlconf)
                )
            )
            path_valid=True
            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                # Insert language after the script prefix and before the
                # rest of the URL
                language_url = request.get_full_path(force_append_slash=path_needs_slash).replace(
                    script_prefix,
                    '%s%s/' % (script_prefix, country or util.get_default_country()),
                    1
                )
                return self.response_redirect_class(language_url)
        elif response.status_code == 404 and country_from_path:
            if request.path_info == "/%s" % country_from_path:
                return self.response_redirect_class("/%s/" % country_from_path)

        if not (country_patterns_used and language_from_path):
            patch_vary_headers(response, ('Accept-Language',))
        if 'Content-Language' not in response:
            response['Content-Language'] = language
        return response
