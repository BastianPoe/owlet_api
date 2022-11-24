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

    google_API_key = 'AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k'
    app_id = 'owa-rg-id'
    app_secret = 'owa-dx85qljgtR6hmVflyrL6LasCxA8'
    owlet_login_url = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='
    owlet_login_token_provider_url = 'https://ayla-sso.owletdata.com/mini/'
    base_user_url = 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json'
    base_properties_url = 'https://ads-owlue1.aylanetworks.com/apiv1/'

    def __init__(self, email=None, password=None):
        """Initialize OwletAPI, with email and password as opt. arguments."""
        self._email = email
        self._password = password
        self._owlet_id_token = None
        self._owlet_refresh_token = None
        self._owlet_id_token_expiry_time = None
        self._owlet_mini_token = None
        self._auth_token = None
        self._refresh_token = None
        self._expiry_time = None
        self._devices = []

    def set_api_key(self, key):
        """Set google API key."""
        self.google_API_key = key

    def set_app_id(self, app_id):
        """Set app_id."""
        self.app_id = app_id

    def set_app_secret(self, app_secret):
        """Set app_secret."""
        self.app_secret = app_secret

    def set_email(self, email):
        """Set Email address aka Username."""
        self._email = email

    def set_password(self, password):
        """Set Password."""
        self._password = password

    def login(self):
        """Login is currently a three step process
            1. Login to Google Identity Toolkit to get owlet_authorization
            2. Use owlet_authorization to get Ayla login token
            3. Use Ayla login token to login to Ayla cloud database
        """

        """Step 1: Login to Google Identity Toolkit to get authorization."""
        login_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        login_url = self.owlet_login_url + self.google_API_key



        login_payload = {
            'returnSecureToken': True,
            'email': self._email,
            'password': self._password
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
        if result.status_code == 400:
            if result.text.__contains__('EMAIL_NOT_FOUND'):
                raise OwletPermanentCommunicationException(
                    'Login failed, bad username', result)
            if result.text.__contains__('INVALID_PASSWORD'):
                raise OwletPermanentCommunicationException(
                    'Login failed, bad password', result)
            if result.text.__contains__('API_KEY_INVALID'):
                raise OwletPermanentCommunicationException(
                    'Login failed, bad API key.', result)
            raise OwletPermanentCommunicationException(
                'Login failed, check username and password', result)
        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Login request failed - status code (' + str(result.status_code) + ') - (Step 2 of 3)', result)

        # Login seems to be ok, extract json
        try:
            json_result = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Server did not send valid json (Step 1 of 3)')

        if ('idToken' not in json_result) or \
           ('refreshToken' not in json_result) or \
           ('expiresIn' not in json_result):
            raise OwletTemporaryCommunicationException(
                'Server did not send id token (Step 1 of 3)', json_result)

        self._owlet_id_token = json_result['idToken']
        self._owlet_refresh_token = json_result['refreshToken']
        self._owlet_id_token_expiry_time = time.time() + int(json_result['expiresIn'])

        """Step 2: Retrieve Ayla Login Token."""
        login_headers = {
            'Accept': 'application/json',
            'authorization': self._owlet_id_token
        }

        login_url = self.owlet_login_token_provider_url

        try:
            result = requests.get(
                login_url,
                headers=login_headers,
                timeout=5
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Login request failed - no response (Step 2 of 3)')

        # Login failed
        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Login request failed - status code (' + str(result.status_code) + ') - (Step 2 of 3)', result)

        # Login seems to be ok, extract json
        try:
            json_result = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Server did not send valid json (Step 2 of 3)')

        if ('mini_token' not in json_result):
            raise OwletTemporaryCommunicationException(
                'Server did not send mini token (Step 2 of 3)', json_result)

        self._owlet_mini_token = json_result['mini_token']

        """Step 3: Login to Ayla and obtain Auth Token."""
        login_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        login_url = self.base_user_url

        login_payload = {
            'token': self._owlet_mini_token,
            'app_id': self.app_id,
            'app_secret': self.app_secret,
            'headers': {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
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
                'Login request failed - no response (Step 3 of 3)', result)

        # Login failed
        if result.status_code != 200:
            if result.status_code == 404 and\
                result.text.__contains__('Could not find application'):
                raise OwletPermanentCommunicationException(
                        'login request failed - app_id or app_secret is bad (Step 3 of 3)', result)
            raise OwletTemporaryCommunicationException(
                'Login request failed - status code (' + str(result.status_code) + ') - (Step 3 of 3)', result)

        # Login seems to be ok, extract json
        try:
            json_result = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Server did not send valid json (Step 3 of 3)')

        if ('access_token' not in json_result) or \
           ('refresh_token' not in json_result) or \
           ('expires_in' not in json_result):
            raise OwletTemporaryCommunicationException(
                'Server did not send access token (Step 3 of 3)', json_result)

        self._auth_token = json_result['access_token']
        self._refresh_token = json_result['refresh_token']
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
                'Server request failed - status code', result)

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
