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
        self.product_name = json['product_name'] if 'product_name' in json else ''
        self.product_class = json['product_class'] if 'product_class' in json else ''
        self.model = json['model'] if 'model' in json else ''
        self.dsn = json['dsn'] if 'dsn' in json else ''
        self.sw_version = json['sw_version'] if 'sw_version' in json else ''
        self.mac = json['mac'] if 'mac' in json else ''
        self.hwsig = json['hwsig'] if 'hwsig' in json else ''
        self.lan_ip = json['lan_ip'] if 'lan_ip' in json else ''
        self.connected_at = json['connected_at'] if 'connected_at' in json else ''
        self.connection_priority = json['connection_priority'] if 'connection_priority' in json else ''
        self.connection_status = json['connection_status'] if 'connection_status' in json else ''
        self.dealer = json['dealer'] if 'dealer' in json else ''
        self.lat = float(json['lat']) if 'lat' in json else ''
        self.lon = float(json['lng']) if 'lng' in json else ''
        self.locality = json['locality'] if 'locality' in json else ''
        self.device_type = json['device_type'] if 'device_type' in json else ''
        self.has_properties = json['has_properties'] if 'has_properties' in json else ''
        self.key = json['key'] if 'key' in json else ''
        self.lan_enabled = json['lan_enabled'] if 'lan_enabled' in json else ''
        self.manuf_model = json['manuf_model'] if 'manuf_model' in json else ''
        self.oem_model = json['oem_model'] if 'oem_model' in json else ''
        self.model = json['model'] if 'model' in json else ''
        self.template_id = json['template_id'] if 'template_id' in json else ''
        self.unique_hardware_id = json['unique_hardware_id'] if 'unique_hardware_id' in json else ''
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
            temp_key = myproperty['property']['key']

            if property_name in self.properties:
                self.properties[property_name].update(myproperty['property'])
            else:
                new_property = OwletProperty(myproperty['property'])
                self.properties[new_property.name] = new_property
                    
            if property_name == 'REAL_TIME_VITALS':
                # Convert Dream Sock Data to Smart Sock 3 Format
                vitals = json.loads(myproperty['property']['value'])

                # OXYGEN_LEVEL = ox
                temp_property = myproperty['property']
                temp_property['name'] = 'OXYGEN_LEVEL'
                temp_property['display_name'] = 'Oxygen Level'
                temp_property['value'] = vitals['ox']
                temp_property['key'] = temp_key + 0.01
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                #HEART_RATE = hr
                temp_property = myproperty['property']
                temp_property['name'] = 'HEART_RATE'
                temp_property['display_name'] = 'Heart Rate'
                temp_property['value'] = vitals['hr']
                temp_property['key'] = temp_key + 0.02
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                #MOVEMENT = mv
                temp_property = myproperty['property']
                temp_property['name'] = 'MOVEMENT'
                temp_property['display_name'] = 'Baby Movement'
                temp_property['value'] = vitals['mv']
                temp_property['key'] = temp_key + 0.03
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # SOCK_CONNECTION = sc
                temp_property = myproperty['property']
                temp_property['name'] = 'SOCK_CONNECTION'
                temp_property['display_name'] = 'Sock Connection'
                temp_property['value'] = vitals['sc']
                temp_property['key'] = temp_key + 0.04
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                """
                # ??? = st
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['st']
                temp_property['key'] = temp_key + 0.05
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """

                # BASE_STAT_ON = bso
                temp_property = myproperty['property']
                temp_property['name'] = 'BASE_STAT_ON'
                temp_property['display_name'] = 'Base Station On'
                temp_property['value'] = vitals['bso']
                temp_property['key'] = temp_key + 0.06
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                #BATT_LEVEL = bat
                temp_property = myproperty['property']
                temp_property['name'] = 'BATT_LEVEL'
                temp_property['display_name'] = 'Battery Level (%)'
                temp_property['value'] = vitals['bat']
                temp_property['key'] = temp_key + 0.07
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # BAT_TIME = btt
                temp_property = myproperty['property']
                temp_property['name'] = 'BAT_TIME'
                temp_property['display_name'] = 'Sock Battery (Minutes)'
                temp_property['value'] = vitals['btt']
                temp_property['key'] = temp_key + 0.08
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # CHARGE_STATUS = chg
                # 1 = Charged
                # 2 = Charging
                temp_property = myproperty['property']
                temp_property['name'] = 'CHARGE_STATUS'
                temp_property['display_name'] = 'Charge Status'
                temp_property['value'] = vitals['chg']
                temp_property['key'] = temp_key + 0.09
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # ALRTS_DISABLED = aps
                temp_property = myproperty['property']
                temp_property['name'] = 'ALRTS_DISABLED'
                temp_property['display_name'] = 'Disable Alerts'
                temp_property['value'] = vitals['aps']
                temp_property['key'] = temp_key + 0.10
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # ALERT = alrt
                # 16 = Disconnected
                # 32 & 64 = Placement
                temp_property = myproperty['property']
                temp_property['name'] = 'ALERT'
                temp_property['display_name'] = 'Alert Status'
                temp_property['value'] = vitals['alrt']
                temp_property['key'] = temp_key + 0.11
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # OTA_STATUS = ota
                # 0 = None
                # 1 = Firmware being sent
                # 2 = Waiting for sock to be plugged in
                # 3 = Installing
                # 4 = Installing Critical
                # 5 = Unknown
                temp_property = myproperty['property']
                temp_property['name'] = 'OTA_STATUS'
                temp_property['display_name'] = 'OTA Status'
                temp_property['value'] = vitals['ota']
                temp_property['key'] = temp_key + 0.12
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                # SOCK_STATUS = srf
                # 1 = Checking On
                # 2 (When sc also = 2) = Kicking
                # 3 = Recently Placed
                temp_property = myproperty['property']
                temp_property['name'] = 'SOCK_STATUS'
                temp_property['display_name'] = 'Sock Status'
                temp_property['value'] = vitals['srf']
                temp_property['key'] = temp_key + 0.13
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property

                #BLE_RSSI = rsi
                temp_property = myproperty['property']
                temp_property['name'] = 'BLE_RSSI'
                temp_property['display_name'] = 'BLE RSSI'
                temp_property['value'] = vitals['rsi']
                temp_property['key'] = temp_key + 0.14
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property 

                """
                # ??? = sb
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['sb']
                temp_property['key'] = temp_key + 0.15
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """

                """
                # ??? = ss
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['ss']
                temp_property['key'] = temp_key + 0.16
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """
                """

                # ??? = mvb
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['mvb']
                temp_property['key'] = temp_key + 0.17
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """
                """

                # ??? = mst
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['mst']
                temp_property['key'] = temp_key + 0.18
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """
                # OXYGEN_TEN_MIN = oxta
                temp_property = myproperty['property']
                temp_property['name'] = 'OXYGEN_TEN_MIN'
                temp_property['display_name'] = 'Oxygen Ten Minute Average'
                temp_property['value'] = vitals['oxta']
                temp_property['key'] = temp_key + 0.19
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """

                # ??? = onm
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['onm']
                temp_property['key'] = temp_key + 0.20
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """
                """

                # ??? = bsb
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['bsb']
                temp_property['key'] = temp_key + 0.21
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """
                """

                # ??? = hw
                temp_property = myproperty['property']
                temp_property['name'] = '???'
                temp_property['display_name'] = '???'
                temp_property['value'] = vitals['hw']
                temp_property['key'] = temp_key + 0.22
                new_property = OwletProperty(temp_property)
                self.properties[new_property.name] = new_property
                """

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
