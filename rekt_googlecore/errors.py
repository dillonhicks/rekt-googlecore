from enum import Enum
from functools import lru_cache

from rekt.utils import snake_case_to_camel_case, read_only_dict

_EXCEPTION_CLASS_NAME_FMT = '{}Error'
exceptions_by_status = {}

class Status(Enum):
    ok = 'OK'
    unknown_error = 'UNKNOWN_ERROR'
    zero_results = 'ZERO_RESULTS'
    over_query_limit = 'OVERY_QUERY_LIMIT'
    request_denied = 'REQUEST_DENIED'
    invalid_request = 'INVALID_REQUEST'
    not_found = 'NOT_FOUND'

    @staticmethod
    @lru_cache(maxsize=1)
    def errors():
        return frozenset({s for s in Status if not s == Status.ok})

class GoogleAPIError(Exception):
    def __init__(self, error_message, response):
        self.error_message = error_message
        self.response = response

    def __str__(self):
        return '{}(error_message={})'.format(self.__class__.__name__, repr(self.error_message))

    def __repr__(self):
        return '<{}>'.format(str(self))


def _exception_class_for_status(status, BaseClass=GoogleAPIError):

    def __init__(self, error_message, response):
        BaseClass.__init__(self, error_message, response)

    exception_name = _EXCEPTION_CLASS_NAME_FMT.format(snake_case_to_camel_case(status.value))
    ExceptionClass = type(exception_name, (BaseClass,), {'__init__' : __init__})

    return ExceptionClass


def _create_exceptions():
    for status in Status.errors():
        ExceptionClass = _exception_class_for_status(status)
        exceptions_by_status[status] = ExceptionClass
        globals()[ExceptionClass.__name__] = ExceptionClass

_create_exceptions()
exceptions_by_status = read_only_dict(exceptions_by_status)

__all__ = ['GoogleAPIError'] + [clazz.__name__ for clazz in exceptions_by_status.values()]
