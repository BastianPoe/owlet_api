#!/usr/bin/env python
"""Contains Class Owlet."""

from json.decoder import JSONDecodeError
import requests
from requests.exceptions import RequestException
from .owletproperty import OwletProperty
from .owletexceptions import OwletTemporaryCommunicationException
from .owletexceptions import OwletNotInitializedException


class Owlet():
    """Class to encapsulate everything related to one Owlet Instance."""

    # pylint: disable=R0902
    def __init__(self, api, json):
        """Initialize Owlet with API reference and json object."""
        self.product_name = json['product_name']
        self.model = json['model']
        self.dsn = json['dsn']
        self.sw_version = json['sw_version']
        self.mac = json['mac']
        self.hwsig = json['hwsig']
        self.lan_ip = json['lan_ip']
        self.connected_at = json['connected_at']
        self.connection_status = json['connection_status']
        self.lat = float(json['lat'])
        self.lon = float(json['lng'])
        self.device_type = json['device_type']
        self.properties = {}
        self.update_interval = 10
        self.owlet_api = api

    def get_property(self, myproperty):
        """Get property of the Owlet."""
        if myproperty in self.properties:
            return self.properties[myproperty]

        return None

    def get_properties(self):
        """Get list of all Owlet properties."""
        return self.properties

    def reactivate(self):
        """(Re-)Activate streaming of Owlet attributes."""
        if not self.properties:
            raise OwletNotInitializedException(
                'Initialize first - no properties')

        if "APP_ACTIVE" not in self.properties:
            raise OwletNotInitializedException(
                'Initialize first - missing property')

        key = self.properties["APP_ACTIVE"].key

        reactivate_url = self.owlet_api.base_properties_url + \
            'properties/{}/datapoints'.format(key)
        reactivate_headers = self.owlet_api.get_request_headers()
        reactivate_payload = {
            "datapoints": {
                "value": 1
            }
        }

        try:
            result = requests.post(
                reactivate_url,
                json=reactivate_payload,
                headers=reactivate_headers,
                timeout=5
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - no response')

        if result.status_code != 201:
            raise OwletTemporaryCommunicationException(
                'Server Request failed, return code %s' % result.status_code)

    def update(self):
        """Update attributes of the Owlet."""
        properties_url = self.owlet_api.base_properties_url + \
            'dsns/{}/properties'.format(self.dsn)

        properties_header = self.owlet_api.get_request_headers()

        try:
            result = requests.get(
                properties_url,
                headers=properties_header
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - no response')

        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - status code')

        try:
            json = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Update failed - JSON error')

        for myproperty in json:
            property_name = myproperty['property']['name']
            if property_name in self.properties:
                self.properties[property_name].update(myproperty['property'])
            else:
                new_property = OwletProperty(myproperty['property'])
                self.properties[new_property.name] = new_property

        for name, myproperty in self.properties.items():
            if name == "APP_ACTIVE":
                continue

            if self.update_interval is None or \
               (myproperty.minimum_update_interval is not None and
                myproperty.minimum_update_interval > 0 and
                myproperty.minimum_update_interval < self.update_interval):
                self.update_interval = myproperty.minimum_update_interval

    def get_update_interval(self):
        """Get interval in seconds when new data is available."""
        return self.update_interval

    def download_logged_data(self):
        """Download "LOGGED_DATA_CACHE", content currently unknown."""
        if not self.properties:
            raise OwletNotInitializedException(
                'Initialize first - no properties')

        if 'LOGGED_DATA_CACHE' not in self.properties:
            raise OwletNotInitializedException(
                'Initialize first - missing property')

        download_url = self.properties['LOGGED_DATA_CACHE'].value
        download_header = self.owlet_api.get_request_headers()

        try:
            result = requests.get(
                download_url,
                headers=download_header,
                timeout=5
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - no answer')

        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - return code')

        try:
            json = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Request failed - JSON invalid')

        if 'datapoint' not in json or \
           'file' not in json['datapoint']:
            raise OwletTemporaryCommunicationException(
                'Request failed - JSON incomplete')

        download_file_url = json['datapoint']['file']

        try:
            result = requests.get(
                download_file_url
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Download Request failed - no answer')

        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Download Request failed - status code')

        return result.text
