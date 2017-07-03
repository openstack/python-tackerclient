# Copyright 2011 VMware, Inc
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tackerclient.i18n import _

"""
Tacker base exception handling.

Exceptions are classified into three categories:
* Exceptions corresponding to exceptions from tacker server:
  This type of exceptions should inherit one of exceptions
  in HTTP_EXCEPTION_MAP.
* Exceptions from client library:
  This type of exceptions should inherit TackerClientException.
* Exceptions from CLI code:
  This type of exceptions should inherit TackerCLIError.
"""


class TackerException(Exception):
    """Base Tacker Exception.

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = _("An unknown exception occurred.")

    def __init__(self, message=None, **kwargs):
        if message:
            self.message = message
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message

    def __str__(self):
        return self._error_string


class TackerClientException(TackerException):
    """Base exception which exceptions from Tacker are mapped into.

    NOTE: on the client side, we use different exception types in order
    to allow client library users to handle server exceptions in try...except
    blocks. The actual error message is the one generated on the server side.
    """

    status_code = 0

    def __init__(self, message=None, **kwargs):
        if 'status_code' in kwargs:
            self.status_code = kwargs['status_code']
        super(TackerClientException, self).__init__(message, **kwargs)


# Base exceptions from Tacker

class BadRequest(TackerClientException):
    status_code = 400


class Unauthorized(TackerClientException):
    status_code = 401
    message = _("Unauthorized: bad credentials.")


class Forbidden(TackerClientException):
    status_code = 403
    message = _("Forbidden: your credentials don't give you access to this "
                "resource.")


class NotFound(TackerClientException):
    status_code = 404


class Conflict(TackerClientException):
    status_code = 409


class InternalServerError(TackerClientException):
    status_code = 500


class ServiceUnavailable(TackerClientException):
    status_code = 503


HTTP_EXCEPTION_MAP = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    500: InternalServerError,
    503: ServiceUnavailable,
}


# Exceptions mapped to Tacker server exceptions
# These are defined if a user of client library needs specific exception.
# Exception name should be <Tacker Exception Name> + 'Client'
# e.g., NetworkNotFound -> NetworkNotFoundClient

class NetworkNotFoundClient(NotFound):
    pass


class PortNotFoundClient(NotFound):
    pass


class StateInvalidClient(BadRequest):
    pass


class NetworkInUseClient(Conflict):
    pass


class PortInUseClient(Conflict):
    pass


class IpAddressInUseClient(Conflict):
    pass


class InvalidIpForNetworkClient(BadRequest):
    pass


class OverQuotaClient(Conflict):
    pass


class IpAddressGenerationFailureClient(Conflict):
    pass


class MacAddressInUseClient(Conflict):
    pass


class ExternalIpAddressExhaustedClient(BadRequest):
    pass


# Exceptions from client library

class NoAuthURLProvided(Unauthorized):
    message = _("auth_url was not provided to the Tacker client")


class EndpointNotFound(TackerClientException):
    message = _("Could not find Service or Region in Service Catalog.")


class EndpointTypeNotFound(TackerClientException):
    message = _("Could not find endpoint type %(type_)s in Service Catalog.")


class AmbiguousEndpoints(TackerClientException):
    message = _("Found more than one matching endpoint in Service Catalog: "
                "%(matching_endpoints)")


class RequestURITooLong(TackerClientException):
    """Raised when a request fails with HTTP error 414."""

    def __init__(self, **kwargs):
        self.excess = kwargs.get('excess', 0)
        super(RequestURITooLong, self).__init__(**kwargs)


class ConnectionFailed(TackerClientException):
    message = _("Connection to tacker failed: %(reason)s")


class SslCertificateValidationError(TackerClientException):
    message = _("SSL certificate validation has failed: %(reason)s")


class MalformedResponseBody(TackerClientException):
    message = _("Malformed response body: %(reason)s")


class InvalidContentType(TackerClientException):
    message = _("Invalid content type %(content_type)s.")


class InvalidInput(TackerClientException):
    message = _("Invalid input: %(reason)s")


# Command line exceptions

class TackerCLIError(TackerException):
    """Exception raised when command line parsing fails."""
    pass


class CommandError(TackerCLIError):
    pass


class UnsupportedVersion(TackerCLIError):
    """Unsupported Version.

    Indicates that the user is trying to use an unsupported version of
    the API.
    """
    pass


class TackerClientNoUniqueMatch(TackerCLIError):
    message = _("Multiple %(resource)s matches found for name '%(name)s',"
                " use an ID to be more specific.")
