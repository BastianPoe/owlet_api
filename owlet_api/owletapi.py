#!/usr/bin/env python
"""Handles Owlet API stuff."""

import time
import requests

from enum import Enum
from firebase import Firebase
from json.decoder import JSONDecodeError
from requests.exceptions import RequestException

from .owlet import Owlet
from .owletexceptions import OwletTemporaryCommunicationException
from .owletexceptions import OwletPermanentCommunicationException
from .owletexceptions import OwletNotInitializedException
from .owletexceptions import OwletConfigurationError


class OwletRegion(Enum):
    US = 1
    EU = 2


class OwletAPI():
    """Handles Owlet API stuff."""

    api_data = {
        OwletRegion.US: {
            "firebase_api_key": "AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA",
            "firebase_database_url": "https://owletcare-prod.firebaseio.com",
            "firebase_storage_bucket": "owletcare-prod.appspot.com",
            "owletdata_signin": "https://ayla-sso.owletdata.com/mini/",
            "owlet_signin": "https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
            "owlet_app_id": "sso-prod-3g-id",
            "owlet_app_secret": "sso-prod-UEjtnPCtFfjdwIwxqnC0OipxRFU",
            "owlet_provider": "owl_id",
            "owlet_properties": "https://ads-field-1a2039d9.aylanetworks.com/apiv1/"
            },
        OwletRegion.EU: {
            "firebase_api_key": "AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM",
            "firebase_database_url": "https://owletcare-prod-eu.firebaseio.com",
            "firebase_storage_bucket": "owletcare-prod-eu.appspot.com",
            "owletdata_signin": "https://ayla-sso.eu.owletdata.com/mini/",
            "owlet_signin": "https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
            "owlet_app_id": "OwletCare-Android-EU-fw-id",
            "owlet_app_secret": "OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw",
            "owlet_provider": "owl_id",
            "owlet_properties": "https://ads-field-eu-1a2039d9.aylanetworks.com/apiv1/"
        }
    }

    def __init__(self, email=None, password=None, region=OwletRegion.US):
        """Initialize OwletAPI, with email and password as opt. arguments."""
        self.set_email(email)
        self.set_password(password)
        self.set_region(region)
        self._auth_token = None
        self._expiry_time = None
        self._devices = []

    def set_email(self, email):
        """Set Emailadress aka Username."""
        self._email = email

    def set_password(self, password):
        """Set Password."""
        self._password = password

    def set_region(self, region):
        """Set Region."""
        if region not in OwletRegion.__members__.values():
            raise OwletConfigurationError("Invalid Owlet region")

        self._region = region

    def get_config(self, region=None):
        if region is None:
            return self.api_data[self._region]

        return self.api_data[region]

    def detect_region(self):
        for region in OwletRegion:
            try:
                self.get_login_jwt(region)
            except OwletPermanentCommunicationException:
                continue

            self.set_region(region)
            return region

        raise OwletPermanentCommunicationException(
                "Unable to detect region. Username or password wrong?")

    def get_login_jwt(self, region=None):
        config = self.get_config(region)
        firebase_config = {
                "apiKey": config['firebase_api_key'],
                "authDomain": None,
                "databaseURL": config['firebase_database_url'],
                "storageBucket": config['firebase_storage_bucket'],
                }

        # Configure firebase
        firebase_auth_instance = Firebase(firebase_config).auth()

        # Login to Firebase
        try:
            login = firebase_auth_instance.sign_in_with_email_and_password(
                    self._email, self._password)
        except requests.exceptions.HTTPError:
            raise OwletPermanentCommunicationException(
                    "Login failed, check username and password")
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                    "Server did not supply valid json, try again")

        # Pull out the JWT
        try:
            json_web_token = login['idToken']
        except KeyError:
            raise OwletTemporaryCommunicationException(
                    "Server did not supply idToken, try again")

        return json_web_token

    def get_login_mini_token(self, json_web_token):
        # Login to owletdata.com
        r = requests.get(
                self.get_config()['owletdata_signin'],
                headers={
                    'Authorization': json_web_token
                    }
                )

        # Pull out the "mini_token" for owletdata.com
        try:
            owletdata_token = r.json()['mini_token']
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                    "Server did not supply valid json, try again")
        except KeyError:
            raise OwletTemporaryCommunicationException(
                    "Server did not supply mini_token, try again")

        return owletdata_token

    def login(self):
        """Login to Owlet Cloud Service and obtain Auth Token."""
        # Log into firebase and receice the JWT
        json_web_token = self.get_login_jwt()

        # Log into owletdata and receive the mini_token
        owletdata_token = self.get_login_mini_token(json_web_token)

        # Log into owlet and receive the access_token
        r = requests.post(
                self.get_config()['owlet_signin'], json={
                    "app_id": self.get_config()['owlet_app_id'],
                    "app_secret": self.get_config()['owlet_app_secret'],
                    "provider": self.get_config()['owlet_provider'],
                    "token": owletdata_token,
                    }
                )

        # Pull out the owlet token
        try:
            self._auth_token = r.json()['access_token']
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                    "Server did not send valid json")
        except KeyError:
            raise OwletTemporaryCommunicationException(
                    "Server did not send access token")

        # Pull out the expiry time
        try:
            self._expiry_time = time.time() + r.json()['expires_in']
        except KeyError:
            self._expiry_time = time.time() + 60

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

        devices_url = self.get_config()['owlet_properties'] + 'devices.json'
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
            try:
                mydevice = device['device']
            except TypeError:
                continue

            new_device = Owlet(self, mydevice)
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
