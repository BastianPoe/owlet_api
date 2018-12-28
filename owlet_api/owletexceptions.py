#!/usr/bin/env python
"""All the exceptions for the Owlet API."""


class OwletException(Exception):
    """Generic Owlet Exception (Base Class)."""


class OwletTemporaryCommunicationException(OwletException):
    """Temporary Communication Problem, please retry later."""


class OwletPermanentCommunicationException(OwletException):
    """Permanent Communication Problem, check your credentials."""


class OwletNotInitializedException(OwletException):
    """Owlet API not initialized yet."""
