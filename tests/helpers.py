"""Helpers for the Omlet Smart Coop tests."""

import requests


def http_error(status: int) -> requests.HTTPError:
    """An HTTPError like the SDK raises from raise_for_status()."""
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(f"{status} error", response=response)
