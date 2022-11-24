#!/usr/bin/env python
"""Contains Class Owlet."""

import json
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
            json_data = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Update failed - JSON error')

        for myproperty in json_data:
            property_name = myproperty['property']['name']
                    
            if property_name == 'REAL_TIME_VITALS':
                # Convert Dream Sock Data to Smart Sock 3 Format
                vitals = json.loads(myproperty['property']['value'])
                # OXYGEN_LEVEL = ox
                temp_property = {
                    'name': 'OXYGEN_LEVEL',
                    'display_name': 'Oxygen Level',
                    'key': myproperty['property']['key'],
                    'value': vitals['ox'],
                    'data_updated_at': myproperty['property']['data_updated_at']
                }
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                #HEART_RATE = hr
                temp_property = {
                    'name': 'HEART_RATE',
                    'display_name': 'Heart Rate',
                    'key': myproperty['property']['key'],
                    'value': vitals['hr'],
                    'data_updated_at': myproperty['property']['data_updated_at']
                }
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                #MOVEMENT = mv
                temp_property = {
                    'name': 'MOVEMENT',
                    'display_name': 'Baby Movement',
                    'key': myproperty['property']['key'],
                    'value': vitals['mv'],
                    'data_updated_at': myproperty['property']['data_updated_at']
                }
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                #BATT_LEVEL = bat
                temp_property = {
                    'name': 'BATT_LEVEL',
                    'display_name': 'Battery Level (%)',
                    'key': myproperty['property']['key'],
                    'value': vitals['bat'],
                    'data_updated_at': myproperty['property']['data_updated_at']
                }
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                #BLE_RSSI = rsi
                temp_property = {
                    'name': 'BLE_RSSI',
                    'display_name': 'BLE RSSI',
                    'key': myproperty['property']['key'],
                    'value': vitals['rsi'],
                    'data_updated_at': myproperty['property']['data_updated_at']
                }
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
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

        if 'LOGGED_DATA_CACHE' not in self.properties and \
            'VITALS_LOG_FILE' not in self.properties:
            raise OwletNotInitializedException(
                'Initialize first - missing property')
        if 'LOGGED_DATA_CACHE' in self.properties:
            download_url = self.properties['LOGGED_DATA_CACHE'].value
        if 'VITALS_LOG_FILE' in self.properties:
            download_url = self.properties['VITALS_LOG_FILE'].value
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
