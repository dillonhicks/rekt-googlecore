import types
import time
from itertools import chain
from functools import partial
from pathlib import Path, PurePath

from pkg_resources import resource_filename

import rekt
from rekt.service import RestClient
from rekt.utils import load_config, api_method_names, _ASYNC_METHOD_PREFIX

from .errors  import Status, exceptions_by_status
from .errors import InvalidRequestError

__all__ = ['GoogleAPIClient']

_API_KEY_ARG_NAME = 'key'
_PAGETOKEN_ARG_NAME = 'pagetoken'
_MAX_PAGES = 3
_MILLIS_PER_SEC = 1000

class GoogleAPIClient(RestClient):
    """
    Base for google api clients that is primed with the api key so you
    do not have to specify it with each request like a raw rekt rest
    client. Further, the google status responses that are not 'OK'
    raise an error with the same name of the status code that share
    the exception class GoogleAPIError for a catch all.
    """
    def __init__(self, rekt_google_module, api_key):
        RestClient.__init__(self)

        self._api_key = api_key
        self._rekt_client = rekt_google_module.Client()
        api_methods = api_method_names(rekt_google_module.resources)

        def build_wrapped_api_method(method_name):
            raw_api_method = getattr(self._rekt_client, method_name)

            def api_call_func(self, **kwargs):
                kwargs[_API_KEY_ARG_NAME] = self._api_key
                response =  raw_api_method(**kwargs)
                try:
                    status = Status[response.status.lower()]
                except (AttributeError, KeyError) as e:                   
                    status = Status.ok

                if status in exceptions_by_status:
                    kwargs.pop(_API_KEY_ARG_NAME, None)
                    raise exceptions_by_status[status](raw_api_method.__name__, kwargs.items(), response.error_message, response)

                return response

            api_call_func.__name__ = raw_api_method.__name__
            api_call_func.__doc__ = raw_api_method.__doc__

            return api_call_func

        def build_wrapped_async_api_method(method_name):

            raw_api_method_name = method_name.replace(_ASYNC_METHOD_PREFIX, '')

            def api_call_func(self, **kwargs):
                raw_api_method = getattr(self, raw_api_method_name)

                def _async_call_handler():
                    return raw_api_method(**kwargs)

                return self._rekt_client._executor.submit(_async_call_handler)

            api_call_func.__name__ = method_name
            api_call_func.__doc__ = getattr(self._rekt_client, raw_api_method_name).__doc__

            return api_call_func


        for method_name in api_methods:
            if method_name.startswith(_ASYNC_METHOD_PREFIX):
                new_method = build_wrapped_async_api_method(method_name)
            else:
                new_method = build_wrapped_api_method(method_name)

            setattr(self, method_name, types.MethodType(new_method, self))


#TODO: Genericize time parameters and errors.
def exponential_retry(call):
    """
    Retry on an InvalidRequestError which will happen if a pagetoken is used before that pagetoken becomes valid.
    """
    base_wait = 333 # ms
    max_wait = 2000 # ms

    last_exception = None

    for attempt in range(5):
        try:
            return call()
        except InvalidRequestError as e:
            last_exception = e
            wait_time = (1 << attempt) * base_wait
            wait_time = min(wait_time, max_wait) # box wait time by the max wait
            wait_time /= _MILLIS_PER_SEC
            time.sleep(wait_time)

    raise last_exception


def paginate_responses(call, max_pages=_MAX_PAGES):
    """
    Assumes that call is the curried api method with the initial
    arguments. This will make a generator based on the api calls that
    require a page token to paginate results. This returned generator
    will yeild a response for each call it is on the caller to do the
    appropriate chaining of results.
    """
    next_page_token = None

    for _ in range(max_pages):

        if next_page_token is None:
            # Do not retry the initial call incase the intial args are bogus
            response = call()
        else:
            # Args are ignored when the pagetoken is given so we have
            # a guarantee that the InvalidRequestError is because the
            # pagetoken is not yet active versus just run of the mill
            # bad params.
            call_with_pagetoken = partial(call, **{_PAGETOKEN_ARG_NAME : next_page_token})
            response = exponential_retry(call_with_pagetoken)

        yield response

        next_page_token = response.next_page_token
        if next_page_token is None:
            break
