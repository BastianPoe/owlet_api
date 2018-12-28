#!/usr/bin/env python
"""Handles Owlet API stuff."""

from json.decoder import JSONDecodeError
import time
import requests
from requests.exceptions import RequestException
from .owlet import Owlet
from .owletexceptions import OwletTemporaryCommunicationException
from .owletexceptions import OwletPermanentCommunicationException
from .owletexceptions import OwletNotInitializedException


class OwletAPI():
    """Handles Owlet API stuff."""

    base_user_url = 'https://user-field.aylanetworks.com/users/'
    base_properties_url = 'https://ads-field.aylanetworks.com/apiv1/'

    def __init__(self, email=None, password=None):
        """Initialize OwletAPI, with email and password as opt. arguments."""
        self._email = email
        self._password = password
        self._auth_token = None
        self._expiry_time = None
        self._devices = []

    def set_email(self, email):
        """Set Emailadress aka Username."""
        self._email = email

    def set_password(self, password):
        """Set Password."""
        self._password = password

    def login(self):
        """Login to Owlet Cloud Service and obtain Auth Token."""
        login_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        login_url = self.base_user_url + 'sign_in.json'

        login_payload = {
            'user': {
                'email': self._email,
                'password': self._password,
                'application': {
                    'app_id': 'OWL-id',
                    'app_secret': 'OWL-4163742'
                }
            }
        }

        try:
            result = requests.post(
                login_url,
                json=login_payload,
                headers=login_headers,
                timeout=5
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Login request failed - no response')

        # Login failed
        if result.status_code == 401:
            raise OwletPermanentCommunicationException(
                'Login failed, check username and password')
        elif result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Login request failed - status code')

        # Login seems to be ok, extract json
        try:
            json_result = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Server did not send valid json')

        if ('access_token' not in json_result) or \
           ('expires_in' not in json_result):
            raise OwletTemporaryCommunicationException(
                'Server did not send access token')

        self._auth_token = json_result['access_token']
        self._expiry_time = time.time() + json_result['expires_in']

    def get_auth_token(self):
        """Get the auth token from the OwletAPI instance."""
        if self._auth_token is None:
            return None

        if self._expiry_time <= time.time():
            self.login()

        return self._auth_token

    def get_request_headers(self):
        """Get array with request headers for subsequent requests."""
        token = self.get_auth_token()

        if token is None:
            return None

        request_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }

        return request_headers

    def update_devices(self):
        """Update list of devices from the cloud."""
        token = self.get_auth_token()

        if token is None:
            raise OwletNotInitializedException('Please login first')

        devices_url = self.base_properties_url + 'devices.json'
        devices_headers = self.get_request_headers()

        try:
            result = requests.get(
                devices_url,
                headers=devices_headers,
                timeout=5
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Server request failed - no response')

        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Server request failed - status code')

        try:
            json_result = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Server did not send valid json')

        self._devices = []

        for device in json_result:
            new_device = Owlet(self, device['device'])
            self._devices.append(new_device)

        return self._devices

    def get_devices(self):
        """Get list of devices (from last update)."""
        if not self._devices:
            self.update_devices()

        return self._devices

    def get_update_interval(self):
        """Get interval in seconds when new data is available."""
        update_interval = None

        for device in self._devices:
            if update_interval is None or \
               (device.get_update_interval() is not None and
                device.get_update_interval() < update_interval):
                update_interval = device.get_update_interval()

        return update_interval
