import types
from itertools import chain
from pathlib import Path, PurePath

from pkg_resources import resource_filename

import rekt
from rekt.service import RestClient
from rekt.utils import load_config, api_method_names

from .errors  import Status, exceptions_by_status

__all__ = ['GoogleAPIClient']


class GoogleAPIClient(RestClient):
    """
    Base for google api clients that is primed with the api key so you
    do not have to specify it with each request like a raw rekt rest
    client. Further, the google status responses that are not 'OK'
    raise an error with the same name of the status code that share
    the exception class GoogleAPIError for a catch all.
    """
    def __init__(self, rekt_google_module, api_key):
        self._api_key = api_key
        self._rekt_client = rekt_google_module.Client()
        api_methods = api_method_names(rekt_google_module.resources)


        def build_wrapped_api_method(method_name):
            raw_api_method = getattr(self._rekt_client, method_name)

            def api_call_func(self, **kwargs):
                kwargs[_API_KEY_ARG_NAME] = self._api_key
                response =  raw_api_method(**kwargs)
                status = Status[response.status]

                if status in exceptions_by_status:
                    raise exceptions_by_status[status](response.error_message, response)

                return response

            api_call_func.__name__ = raw_api_method.__name__
            api_call_func.__doc__ = raw_api_method.__doc__

            return api_call_func

        for method_name in api_methods:
            new_method = build_wrapped_api_method(method_name)
            setattr(self, method_name, types.MethodType(new_method, self))
