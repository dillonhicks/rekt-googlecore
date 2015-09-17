import types
from itertools import chain
from pathlib import Path, PurePath

from pkg_resources import resource_filename

import rekt
from rekt.service import RestClient
from rekt.utils import load_config, api_method_names

from . import specs

__all__ = ['GooglePlacesClient']

_googleplaces = rekt.load_service(rekt.utils.load_config('googleplaces'))
_API_KEY_ARG_NAME = 'key'

def _load_builtin_config():
    config_path = Path(next(iter(specs.__path__)))
    config_path = config_path / PurePath(resource_filename('rekt_googeplaces.specs', 'googleplaces.yaml'))
    return load_config(config_path)


class GooglePlacesClient(RestClient):
    """
    TODO: make this generic so you can make it a wrapper
    """
    def __init__(self, api_key):
        self._api_key = api_key
        self._rekt_client = _googleplaces.Client()
        api_methods = api_method_names(_googleplaces.resources)

        def build_wrapped_api_method(method_name):
            raw_api_method = getattr(self._rekt_client, method_name)

            def api_call_func(self, **kwargs):
                kwargs[_API_KEY_ARG_NAME] = self._api_key
                return raw_api_method(**kwargs)

            api_call_func.__name__ = raw_api_method.__name__
            api_call_func.__doc__ = raw_api_method.__doc__

            return api_call_func

        for method_name in api_methods:
            new_method = build_wrapped_api_method(method_name)
            setattr(self, method_name, types.MethodType(new_method, self))
