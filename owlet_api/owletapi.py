#!/usr/bin/env python
"""Handles Owlet API stuff."""

import json
from json.decoder import JSONDecodeError
import time
import calendar
import requests
from requests.exceptions import RequestException
import sqlite3
from .owlet import Owlet
from .owletpropertydatapoint import OwletPropertyDatapoint
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
    
    #By default vital data is returned in 10 minute increments. Change here if different time is desired
    vital_data_resolution = 600

    def __init__(self, email=None, password=None):
        """Initialize OwletAPI, with email and password as opt. arguments."""
        self._email = email
        self._password = password
        self._owlet_id_token = None
        self._owlet_local_id = None
        self._owlet_refresh_token = None
        self._owlet_id_token_expiry_time = None
        self._owlet_mini_token = None
        self._auth_token = None
        self._refresh_token = None
        self._expiry_time = None
        self._devices = []

    def set_vital_data_resolution(self, time):
        """Set vital data time resolution."""
        self.vital_data_resolution = time

    def set_api_key(self, key):
        """Set google API key."""
        self.google_API_key = key

    def set_app_id(self, app_id):
        """Set app_id."""
        self.app_id = app_id

    def set_app_secret(self, app_secret):
        """Set app_secret."""
        self.app_secret = app_secret

    def set_owlet_login_url(self, owlet_login_url):
        """Set owlet_login_url."""
        self.owlet_login_url = owlet_login_url

    def set_owlet_login_token_provider_url(self, owlet_login_token_provider_url):
        """Set owlet_login_token_provider_url."""
        self.owlet_login_token_provider_url = owlet_login_token_provider_url

    def set_base_user_url(self, base_user_url):
        """Set base_user_url."""
        self.base_user_url = base_user_url

    def set_base_properties_url(self, base_properties_url):
        """Set base_properties_url."""
        self.base_properties_url = base_properties_url

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
           ('localId' not in json_result) or \
           ('refreshToken' not in json_result) or \
           ('expiresIn' not in json_result):
            raise OwletTemporaryCommunicationException(
                'Server did not send id token (Step 1 of 3)', json_result)

        self._owlet_id_token = json_result['idToken']
        self._owlet_local_id = json_result['localId']
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
    
    def create_db_structure(self, con, cur):
        #Setup Database if it isn't already setup
        cur.execute("CREATE TABLE IF NOT EXISTS device(connected_at,connection_priority,connection_status,dealer,device_type,dsn,has_properties,hwsig,key,lan_enabled,lan_ip,lat,lng,locality,mac,manuf_model,model,oem_model,product_class,product_name,sw_version,template_id,unique_hardware_id, PRIMARY KEY(key), UNIQUE(dsn))")
        cur.execute("CREATE TABLE IF NOT EXISTS device_properties(type,name,base_type,read_only,direction,scope,data_updated_at,key,device_key,product_name,track_only_changes,display_name,host_sw_version,time_series,derived,app_type,recipe,value,generated_from,generated_at,denied_roles,ack_enabled,retention_days,ack_status,ack_message,acked_at, PRIMARY KEY(key,data_updated_at))")
        cur.execute("CREATE TABLE IF NOT EXISTS device_property_datapoints(device_dsn,property_name,id,updated_at,created_at,created_at_from_device,echo,metadata,generated_at,generated_from,value,acked_at,ack_status,ack_message, PRIMARY KEY(id))")
        cur.execute("CREATE TABLE IF NOT EXISTS events (createTime,deviceType,eventType,isDiscrete,isUserModified,name,profile,profileType,service,serviceType,startTime,updateTime, PRIMARY KEY(name))")
        cur.execute("CREATE TABLE IF NOT EXISTS sleep_state_summary(endTime,longestSleepSegmentMinutes,sessionType,sleepOnsetMinutes,sleepQuality,sleepStateDurationsMinutes,startTime,wakingsCount,awakeStateDurationsMinutes,lightSleepStateDurationsMinutes,deepSleepStateDurationsMinutes, PRIMARY KEY(startTime,endTime))")
        cur.execute("CREATE TABLE IF NOT EXISTS sleep_state_detail(summary_startTime, summary_endTime, timeWindowStartTime, sleepState, PRIMARY KEY(summary_startTime, summary_endTime, timeWindowStartTime))")
        cur.execute("CREATE TABLE IF NOT EXISTS vital_data(event_startTime,validSampleCount,firstReadingTime,heartRate_avg,heartRate_max,heartRate_min,lastReadingTime,movement_avg,oxygen_avg,oxygen_max,oxygen_min,timeWindowStartTime, PRIMARY KEY(event_startTime,timeWindowStartTime))")
        con.commit()

    def save_device_to_db(self, con, cur, device):
        cur.execute('INSERT into device (\
                connected_at,\
                connection_priority,\
                connection_status,\
                dealer,\
                device_type,\
                dsn,\
                has_properties,\
                hwsig,\
                key,\
                lan_enabled,\
                lan_ip,\
                lat,\
                lng,\
                locality,\
                mac,\
                manuf_model,\
                model,\
                oem_model,\
                product_class,\
                product_name,\
                sw_version,\
                template_id,\
                unique_hardware_id\
            )\
                VALUES (\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?\
            )\
            on conflict ("key") do \
            UPDATE\
            SET\
                connected_at = ?,\
                connection_priority = ?,\
                connection_status = ?,\
                dealer = ?,\
                device_type = ?,\
                dsn = ?,\
                has_properties = ?,\
                hwsig = ?,\
                key = ?,\
                lan_enabled = ?,\
                lan_ip = ?,\
                lat = ?,\
                lng = ?,\
                locality = ?,\
                mac = ?,\
                manuf_model = ?,\
                model = ?,\
                oem_model = ?,\
                product_class = ?,\
                product_name = ?,\
                sw_version = ?,\
                template_id = ?,\
                unique_hardware_id = ?\
            ',(device.connected_at,\
                json.dumps(device.connection_priority),\
                device.connection_status,\
                device.dealer,\
                device.device_type,\
                device.dsn,\
                device.has_properties,\
                device.hwsig,\
                device.key,\
                device.lan_enabled,\
                device.lan_ip,\
                device.lat,\
                device.lon,\
                device.locality,\
                device.mac,\
                device.manuf_model,\
                device.model,\
                device.oem_model,\
                device.product_class,\
                device.product_name,\
                device.sw_version,\
                device.template_id,\
                device.unique_hardware_id,\
                \
                device.connected_at,\
                json.dumps(device.connection_priority),\
                device.connection_status,\
                device.dealer,\
                device.device_type,\
                device.dsn,\
                device.has_properties,\
                device.hwsig,\
                device.key,\
                device.lan_enabled,\
                device.lan_ip,\
                device.lat,\
                device.lon,\
                device.locality,\
                device.mac,\
                device.manuf_model,\
                device.model,\
                device.oem_model,\
                device.product_class,\
                device.product_name,\
                device.sw_version,\
                device.template_id,\
                device.unique_hardware_id)
            )
        con.commit()

    def save_device_property_to_db(self, con, cur, property):
        cur.execute('INSERT into device_properties (\
                type,\
                name,\
                base_type,\
                read_only,\
                direction,\
                scope,\
                data_updated_at,\
                key,\
                device_key,\
                product_name,\
                track_only_changes,\
                display_name,\
                host_sw_version,\
                time_series,\
                derived,\
                app_type,\
                recipe,\
                value,\
                generated_from,\
                generated_at,\
                denied_roles,\
                ack_enabled,\
                retention_days,\
                ack_status,\
                ack_message,\
                acked_at\
            )\
                VALUES (\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?\
            )\
            on conflict ("key", "data_updated_at") do \
            UPDATE\
            SET\
                type=?,\
                name=?,\
                base_type=?,\
                read_only=?,\
                direction=?,\
                scope=?,\
                data_updated_at=?,\
                key=?,\
                device_key=?,\
                product_name=?,\
                track_only_changes=?,\
                display_name=?,\
                host_sw_version=?,\
                time_series=?,\
                derived=?,\
                app_type=?,\
                recipe=?,\
                value=?,\
                generated_from=?,\
                generated_at=?,\
                denied_roles=?,\
                ack_enabled=?,\
                retention_days=?,\
                ack_status=?,\
                ack_message=?,\
                acked_at=?\
            ',(property.type,\
                property.name,\
                property.base_type,\
                property.read_only,\
                property.direction,\
                property.scope,\
                property.data_updated_at,\
                property.key,\
                property.device_key,\
                property.product_name,\
                property.track_only_changes,\
                property.display_name,\
                property.host_sw_version,\
                property.time_series,\
                property.derived,\
                property.app_type,\
                property.recipe,\
                property.value,\
                property.generated_from,\
                property.generated_at,\
                json.dumps(property.denied_roles),\
                property.ack_enabled,\
                property.retention_days,\
                property.ack_status,\
                property.ack_message,\
                property.acked_at,\
                \
                property.type,\
                property.name,\
                property.base_type,\
                property.read_only,\
                property.direction,\
                property.scope,\
                property.data_updated_at,\
                property.key,\
                property.device_key,\
                property.product_name,\
                property.track_only_changes,\
                property.display_name,\
                property.host_sw_version,\
                property.time_series,\
                property.derived,\
                property.app_type,\
                property.recipe,\
                property.value,\
                property.generated_from,\
                property.generated_at,\
                json.dumps(property.denied_roles),\
                property.ack_enabled,\
                property.retention_days,\
                property.ack_status,\
                property.ack_message,\
                property.acked_at)
            )
        con.commit()
    
    def save_device_property_datapoints_to_db(self, con, cur, dsn, property_name):
        cur.execute("select MAX(created_at) as max, MIN(created_at) as min FROM device_property_datapoints WHERE device_dsn = '{}' and property_name = '{}'".format(dsn,property_name))
        max_date,min_date = cur.fetchone()
        max_date = "&filter[created_at_since_date]="+max_date if max_date != None else ''
        min_date = "&filter[created_at_end_date]="+min_date if min_date != None else ''
        #Get datapoints newer than those already in DB
        self.save_device_property_datapoints_to_db_by_range(con, cur, dsn, property_name, max_date)

        #No need to run this the earlier run already collected them all.
        if max_date != "":
            #Get datapoints older than those already in DB
            self.save_device_property_datapoints_to_db_by_range(con, cur, dsn, property_name, min_date)

    def save_device_property_datapoints_to_db_by_range(self, con, cur, dsn, property_name, filter):
        next_page = ""
        while True:
            cur.execute("begin")
            """Get the Properties Datapoints."""
            datapoints_url = self.base_properties_url + \
                'dsns/{}/properties/{}/datapoints.json?paginated=true&is_forward_page=true{}{}'.format(dsn,property_name,next_page,filter)

            properties_header = self.get_request_headers()

            try:
                result = requests.get(
                    datapoints_url,
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
            next_page = "&next="+json_data["meta"]["next_page"] if json_data["meta"]["next_page"] != None else None
            for mydatapoint in json_data["datapoints"]:
                new_property = OwletPropertyDatapoint(mydatapoint['datapoint'])
                self.save_individual_device_property_datapoint_to_db(cur,con,new_property,dsn,property_name)

                #Expand new format datapoints to old format
                if property_name == 'REAL_TIME_VITALS':
                    # Convert Dream Sock Data to Smart Sock 3 Format
                    vitals = json.loads(new_property.value)

                    # OXYGEN_LEVEL = ox
                    temp_property = new_property
                    temp_property.value = vitals['ox'] if 'ox' in vitals else ''
                    temp_property.id = new_property.id + '0.01'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'OXYGEN_LEVEL')

                    #HEART_RATE = hr
                    temp_property = new_property
                    new_property.value = vitals['hr'] if 'hr' in vitals else ''
                    temp_property.id = new_property.id + '0.02'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'HEART_RATE')

                    #MOVEMENT = mv
                    temp_property = new_property
                    new_property.value = vitals['mv'] if 'mv' in vitals else ''
                    temp_property.id = new_property.id + '0.03'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'MOVEMENT')

                    # SOCK_CONNECTION = sc
                    temp_property = new_property
                    new_property.value = vitals['sc'] if 'sc' in vitals else ''
                    temp_property.id = new_property.id + '0.04'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'SOCK_CONNECTION')

                    """
                    # ??? = st
                    temp_property = new_property
                    new_property.value = vitals['st'] if 'st' in vitals else ''
                    temp_property.id = new_property.id + '0.05'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """

                    # BASE_STAT_ON = bso
                    temp_property = new_property
                    new_property.value = vitals['bso'] if 'bso' in vitals else ''
                    temp_property.id = new_property.id + '0.06'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'BASE_STAT_ON')

                    #BATT_LEVEL = bat
                    temp_property = new_property
                    new_property.value = vitals['bat'] if 'bat' in vitals else ''
                    temp_property.id = new_property.id + '0.07'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'BATT_LEVEL')

                    # BAT_TIME = btt
                    temp_property = new_property
                    new_property.value = vitals['btt'] if 'btt' in vitals else ''
                    temp_property.id = new_property.id + '0.08'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'BAT_TIME')

                    # CHARGE_STATUS = chg
                    # 1 = Charged
                    # 2 = Charging
                    temp_property = new_property
                    new_property.value = vitals['chg'] if 'chg' in vitals else ''
                    temp_property.id = new_property.id + '0.09'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'CHARGE_STATUS')

                    # ALRTS_DISABLED = aps
                    temp_property = new_property
                    new_property.value = vitals['aps'] if 'aps' in vitals else ''
                    temp_property.id = new_property.id + '0.10'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'ALRTS_DISABLED')

                    # ALERT = alrt
                    # 16 = Disconnected
                    # 32 & 64 = Placement
                    temp_property = new_property
                    new_property.value = vitals['alrt'] if 'alrt' in vitals else ''
                    temp_property.id = new_property.id + '0.11'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'ALERT')

                    # OTA_STATUS = ota
                    # 0 = None
                    # 1 = Firmware being sent
                    # 2 = Waiting for sock to be plugged in
                    # 3 = Installing
                    # 4 = Installing Critical
                    # 5 = Unknown
                    temp_property = new_property
                    new_property.value = vitals['ota'] if 'ota' in vitals else ''
                    temp_property.id = new_property.id + '0.12'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'OTA_STATUS')

                    # SOCK_STATUS = srf
                    # 1 = Checking On
                    # 2 (When sc also = 2) = Kicking
                    # 3 = Recently Placed
                    temp_property = new_property
                    new_property.value = vitals['srf'] if 'srf' in vitals else ''
                    temp_property.id = new_property.id + '0.13'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'SOCK_STATUS')

                    #BLE_RSSI = rsi
                    temp_property = new_property
                    new_property.value = vitals['rsi'] if 'rsi' in vitals else ''
                    temp_property.id = new_property.id + '0.14'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'BLE_RSSI')

                    """
                    # ??? = sb
                    temp_property = new_property
                    new_property.value = vitals['sb'] if 'sb' in vitals else ''
                    temp_property.id = new_property.id + '0.15'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """

                    """
                    # ??? = ss
                    temp_property = new_property
                    new_property.value = vitals['ss'] if 'ss' in vitals else ''
                    temp_property.id = new_property.id + '0.16'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """
                    """

                    # ??? = mvb
                    temp_property = new_property
                    new_property.value = vitals['mvb'] if 'mvb' in vitals else ''
                    temp_property.id = new_property.id + '0.17'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """
                    """

                    # ??? = mst
                    temp_property = new_property
                    new_property.value = vitals['mst'] if 'mst' in vitals else ''
                    temp_property.id = new_property.id + '0.18'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """
                    # OXYGEN_TEN_MIN = oxta
                    temp_property = new_property
                    new_property.value = vitals['oxta'] if 'oxta' in vitals else ''
                    temp_property.id = new_property.id + '0.19'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'OXYGEN_TEN_MIN')
                    """

                    # ??? = onm
                    temp_property = new_property
                    new_property.value = vitals['onm'] if 'onm' in vitals else ''
                    temp_property.id = new_property.id + '0.20'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """
                    """

                    # ??? = bsb
                    temp_property = new_property
                    new_property.value = vitals['bsb'] if 'bsb' in vitals else ''
                    temp_property.id = new_property.id + '0.21'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """
                    """

                    # ??? = hw
                    temp_property = new_property
                    new_property.value = vitals['hw'] if 'hw' in vitals else ''
                    temp_property.id = new_property.id + '0.22'
                    self.save_individual_device_property_datapoint_to_db(cur,con,temp_property,dsn,'???')
                    """
            cur.execute("commit")
            con.commit()
            if next_page == None:
                break            
            print(".", end ="")
            
    
    def save_individual_device_property_datapoint_to_db(self, cur, con, new_property, dsn, property_name):
        #Add data to database
        cur.execute('INSERT into device_property_datapoints (\
                device_dsn,\
                property_name,\
                id,\
                updated_at,\
                created_at,\
                created_at_from_device,\
                echo,\
                metadata,\
                generated_at,\
                generated_from,\
                value,\
                acked_at,\
                ack_status,\
                ack_message\
            )\
                VALUES (\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?,\
                ?\
            )\
            on conflict ("id") do \
            UPDATE\
            SET\
                device_dsn=?,\
                property_name=?,\
                id=?,\
                updated_at=?,\
                created_at=?,\
                created_at_from_device=?,\
                echo=?,\
                metadata=?,\
                generated_at=?,\
                generated_from=?,\
                value=?,\
                acked_at=?,\
                ack_status=?,\
                ack_message=?\
            ',(dsn,\
                property_name,\
                new_property.id,\
                new_property.updated_at,\
                new_property.created_at,\
                new_property.created_at_from_device,\
                new_property.echo,\
                json.dumps(new_property.metadata),\
                new_property.generated_at,\
                new_property.generated_from,\
                new_property.value,\
                new_property.acked_at,\
                new_property.ack_status,\
                new_property.ack_message,\
                \
                dsn,\
                property_name,\
                new_property.id,\
                new_property.updated_at,\
                new_property.created_at,\
                new_property.created_at_from_device,\
                new_property.echo,\
                json.dumps(new_property.metadata),\
                new_property.generated_at,\
                        new_property.generated_from,\
                        new_property.value,\
                        new_property.acked_at,\
                        new_property.ack_status,\
                        new_property.ack_message)
                    )

    def save_events_to_db(self, con, cur, event_type = ""):
        #potential SQL injection error here that I am currently ignoring
        secondary_filter_sql = " where eventType = '{}'".format(event_type) if event_type != '' else ''
        secondary_filter_web = "eventType%20%3D%20{}%20AND%20".format(event_type) if event_type != '' else ''

        count = limit = 100

        while count > 0:
            cur.execute("begin")

            cur.execute("select MAX(startTime) as max, MIN(startTime) as min FROM events{}".format(secondary_filter_sql))
            max_date,min_date = cur.fetchone()
            filter = "&filter={}(startTime%20%3E%20{}Z%20OR%20startTime%20%3C%20{}Z)".format(secondary_filter_web, max_date[0:19],min_date[0:19]) if max_date != None else ''
            if filter == "" and secondary_filter_web != "":
                filter = "&filter={}".format(secondary_filter_web[0:-9])

            #Get Events
            events_url = 'https://accounts.owletdata.com/v2/accounts/{}/events?totalSize={}{}'.format(self._owlet_local_id, limit, filter)

            """Get the Events."""
            properties_header = {
                'Accept': 'application/json',
                'Authorization': 'Bearer {}'.format(self._owlet_id_token)
            }

            try:
                result = requests.get(
                    events_url,
                    headers=properties_header
                )
            except RequestException:
                raise OwletTemporaryCommunicationException(
                    'Server Request failed - no response')
            if result.status_code == 598:
                #Temporary read error wait 30 seconds and try again
                time.sleep(30)
                
                #Close out DB transactions
                cur.execute("commit")
                con.commit()

                self.save_events_to_db(con, cur)
                #Exit loop since error ocurred
                break
            if result.status_code != 200:
                raise OwletTemporaryCommunicationException(
                    'Server Request failed - status code')

            try:
                json_data = result.json()
                count = len(json_data["events"])
            except JSONDecodeError:
                raise OwletTemporaryCommunicationException(
                    'Update failed - JSON error')
            for mydatapoint in json_data["events"]:
                #Lookup details first to allow for resuming upon error
                if mydatapoint["eventType"] == "EVENT_TYPE_PROFILE_SLEEP":
                    self.save_sleep_summary_data_to_db(con, cur, mydatapoint["profile"], mydatapoint["startTime"])
                    self.save_vital_summary_data_to_db(con, cur, mydatapoint["profile"], mydatapoint["startTime"])
                
                #Add data to database
                cur.execute('INSERT into events (\
                        createTime,\
                        deviceType,\
                        eventType,\
                        isDiscrete,\
                        isUserModified,\
                        name,\
                        profile,\
                        profileType,\
                        service,\
                        serviceType,\
                        startTime,\
                        updateTime\
                    )\
                        VALUES (\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?,\
                        ?\
                    )\
                    on conflict ("name") do \
                    UPDATE\
                    SET\
                        createTime=?,\
                        deviceType=?,\
                        eventType=?,\
                        isDiscrete=?,\
                        isUserModified=?,\
                        name=?,\
                        profile=?,\
                        profileType=?,\
                        service=?,\
                        serviceType=?,\
                        startTime=?,\
                        updateTime=?\
                    ',(mydatapoint["createTime"] if 'createTime' in mydatapoint else '',\
                        mydatapoint["deviceType"] if 'deviceType' in mydatapoint else '',\
                        mydatapoint["eventType"] if 'eventType' in mydatapoint else '',\
                        mydatapoint["isDiscrete"] if 'isDiscrete' in mydatapoint else '',\
                        mydatapoint["isUserModified"] if 'isUserModified' in mydatapoint else '',\
                        mydatapoint["name"] if 'name' in mydatapoint else '',\
                        mydatapoint["profile"] if 'profile' in mydatapoint else '',\
                        mydatapoint["profileType"] if 'profileType' in mydatapoint else '',\
                        mydatapoint["service"] if 'service' in mydatapoint else '',\
                        mydatapoint["serviceType"] if 'serviceType' in mydatapoint else '',\
                        mydatapoint["startTime"] if 'startTime' in mydatapoint else '',\
                        mydatapoint["updateTime"] if 'updateTime' in mydatapoint else '',\
                        \
                        mydatapoint["createTime"] if 'createTime' in mydatapoint else '',\
                        mydatapoint["deviceType"] if 'deviceType' in mydatapoint else '',\
                        mydatapoint["eventType"] if 'eventType' in mydatapoint else '',\
                        mydatapoint["isDiscrete"] if 'isDiscrete' in mydatapoint else '',\
                        mydatapoint["isUserModified"] if 'isUserModified' in mydatapoint else '',\
                        mydatapoint["name"] if 'name' in mydatapoint else '',\
                        mydatapoint["profile"] if 'profile' in mydatapoint else '',\
                        mydatapoint["profileType"] if 'profileType' in mydatapoint else '',\
                        mydatapoint["service"] if 'service' in mydatapoint else '',\
                        mydatapoint["serviceType"] if 'serviceType' in mydatapoint else '',\
                        mydatapoint["startTime"] if 'startTime' in mydatapoint else '',\
                        mydatapoint["updateTime"] if 'updateTime' in mydatapoint else '')
                    )
            cur.execute("commit")
            con.commit()
        con.commit()
        
    def save_sleep_summary_data_to_db(self, con, cur, profile, start_time):
        #Convert start_time to timestamp
        temp_time = time.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
        start_timestamp = calendar.timegm(temp_time)
        #Calculate end_time
        end_timestamp = start_timestamp + 86400

        #Get Sleep Summary Data
        events_url = 'https://sleep-data.owletdata.com/v1/{}/sleep?endTime={}&startTime={}&timeZone=GMT&version=smartSock3Sleep'.format(profile,end_timestamp,start_timestamp)
        """Get the Events."""
        properties_header = {
            'Accept': 'application/json',
            'Authorization': '{}'.format(self._owlet_id_token)
        }

        try:
            result = requests.get(
                events_url,
                headers=properties_header
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - no response')
        if result.status_code == 598:
            #Temporary read error try again
            self.save_sleep_summary_data_to_db(con, cur, profile, start_time)
            #Exit loop since error ocurred
            return
        if result.status_code == 429:
            #To many requests 
            wait_time = 20 if result.raw.retries.DEFAULT_BACKOFF_MAX else 120
            print("To many requests waiting "+wait_time+" to try again.")
            time.sleep(wait_time)   #wait the recommended 2 minutes and try again         
            self.save_sleep_summary_data_to_db(con, cur, profile, start_time)
            #Exit loop since error ocurred
            return
        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - status code')

        try:
            json_data = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Update failed - JSON error')
        for mydatapoint in json_data["sessions"]:
            #Add data to database
            cur.execute('INSERT into sleep_state_summary (\
                    endTime,\
                    longestSleepSegmentMinutes,\
                    sessionType,\
                    sleepOnsetMinutes,\
                    sleepQuality,\
                    sleepStateDurationsMinutes,\
                    startTime,\
                    wakingsCount,\
                    awakeStateDurationsMinutes,\
                    lightSleepStateDurationsMinutes,\
                    deepSleepStateDurationsMinutes\
                )\
                    VALUES (\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?\
                )\
                on conflict ("startTime", "endTime") do \
                UPDATE\
                SET\
                    endTime=?,\
                    longestSleepSegmentMinutes=?,\
                    sessionType=?,\
                    sleepOnsetMinutes=?,\
                    sleepQuality=?,\
                    sleepStateDurationsMinutes=?,\
                    startTime=?,\
                    wakingsCount=?,\
                    awakeStateDurationsMinutes=?,\
                    lightSleepStateDurationsMinutes=?,\
                    deepSleepStateDurationsMinutes=?\
                ',(mydatapoint["endTime"] if 'endTime' in mydatapoint else '',\
                    mydatapoint["longestSleepSegmentMinutes"] if 'longestSleepSegmentMinutes' in mydatapoint else '',\
                    mydatapoint["sessionType"] if 'sessionType' in mydatapoint else '',\
                    mydatapoint["sleepOnsetMinutes"] if 'sleepOnsetMinutes' in mydatapoint else '',\
                    mydatapoint["sleepQuality"] if 'sleepQuality' in mydatapoint else '',\
                    json.dumps(mydatapoint["sleepStateDurationsMinutes"]) if 'sleepStateDurationsMinutes' in mydatapoint else '',\
                    mydatapoint["startTime"] if 'startTime' in mydatapoint else '',\
                    mydatapoint["wakingsCount"] if 'wakingsCount' in mydatapoint else '',\
                    mydatapoint["sleepStateDurationsMinutes"]['1'] if '1' in mydatapoint["sleepStateDurationsMinutes"] else '',\
                    mydatapoint["sleepStateDurationsMinutes"]['8'] if '8' in mydatapoint["sleepStateDurationsMinutes"] else '',\
                    mydatapoint["sleepStateDurationsMinutes"]['15'] if '15' in mydatapoint["sleepStateDurationsMinutes"] else '',\
                    \
                    mydatapoint["endTime"] if 'endTime' in mydatapoint else '',\
                    mydatapoint["longestSleepSegmentMinutes"] if 'longestSleepSegmentMinutes' in mydatapoint else '',\
                    mydatapoint["sessionType"] if 'sessionType' in mydatapoint else '',\
                    mydatapoint["sleepOnsetMinutes"] if 'sleepOnsetMinutes' in mydatapoint else '',\
                    mydatapoint["sleepQuality"] if 'sleepQuality' in mydatapoint else '',\
                    json.dumps(mydatapoint["sleepStateDurationsMinutes"]) if 'sleepStateDurationsMinutes' in mydatapoint else '',\
                    mydatapoint["startTime"] if 'startTime' in mydatapoint else '',\
                    mydatapoint["wakingsCount"] if 'wakingsCount' in mydatapoint else '',\
                    mydatapoint["sleepStateDurationsMinutes"]['1'] if '1' in mydatapoint["sleepStateDurationsMinutes"] else '',\
                    mydatapoint["sleepStateDurationsMinutes"]['8'] if '8' in mydatapoint["sleepStateDurationsMinutes"] else '',\
                    mydatapoint["sleepStateDurationsMinutes"]['15'] if '15' in mydatapoint["sleepStateDurationsMinutes"] else '')
                )
        count = len(json_data["data"]["timeWindowStartTimes"])
        for x in range(count):
            summary_startTime = json_data["sessions"][0]["startTime"]
            summary_endTime = json_data["sessions"][0]["endTime"]
            timeWindowStartTime = json_data["data"]["timeWindowStartTimes"][x]
            sleepState = json_data["data"]["sleepStates"][x]
            cur.execute('INSERT into sleep_state_detail (\
                    summary_startTime,\
                    summary_endTime,\
                    timeWindowStartTime,\
                    sleepState\
                )\
                    VALUES (\
                    ?,\
                    ?,\
                    ?,\
                    ?\
                )\
                on conflict (summary_startTime, summary_endTime, timeWindowStartTime) do \
                UPDATE\
                SET\
                    summary_startTime=?,\
                    summary_endTime=?,\
                    timeWindowStartTime=?,\
                    sleepState=?\
                ',(summary_startTime if summary_startTime != "" else '',\
                   summary_endTime if summary_startTime != "" else '',\
                   timeWindowStartTime if timeWindowStartTime != "" else '',\
                   sleepState if sleepState != "" else '',\
                    \
                   summary_startTime if summary_startTime != "" else '',\
                   summary_endTime if summary_startTime != "" else '',\
                   timeWindowStartTime if timeWindowStartTime != "" else '',\
                   sleepState if sleepState != "" else '')
                )

    def save_vital_summary_data_to_db(self, con, cur, profile, start_time):
        #Convert start_time to timestamp
        temp_time = time.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
        start_timestamp = calendar.timegm(temp_time)
        #Calculate end_time
        end_timestamp = start_timestamp + 86400

        #Get Vitals Data
        events_url = 'https://vital-data.owletdata.com/v1/{}/vitals?resolution={}&startTime={}&version=smartSock3Sleep&endTime={}'.format(profile,self.vital_data_resolution,start_timestamp,end_timestamp)
        """Get the Events."""
        properties_header = {
            'Accept': 'application/json',
            'Authorization': '{}'.format(self._owlet_id_token)
        }

        try:
            result = requests.get(
                events_url,
                headers=properties_header
            )
        except RequestException:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - no response')
        if result.status_code == 598:
            #Temporary read error try again
            self.save_vital_summary_data_to_db(con, cur, profile, start_time)
            #Exit loop since error ocurred
            return
        if result.status_code != 200:
            raise OwletTemporaryCommunicationException(
                'Server Request failed - status code')

        try:
            json_data = result.json()
        except JSONDecodeError:
            raise OwletTemporaryCommunicationException(
                'Update failed - JSON error')
        count = len(json_data["data"]["timeWindowStartTimes"])
        for x in range(count):
            event_startTime = start_time
            validSampleCount = json_data["data"]["counts"]["validSamples"][x]
            firstReadingTime = json_data["data"]["firstReadingTimes"][x]
            heartRate_avg = json_data["data"]["heartRate"]["avg"][x]
            heartRate_max = json_data["data"]["heartRate"]["max"][x]
            heartRate_min = json_data["data"]["heartRate"]["min"][x]
            lastReadingTime = json_data["data"]["lastReadingTimes"][x]
            movement_avg = json_data["data"]["movement"]["avg"][x]
            oxygen_avg = json_data["data"]["oxygen"]["avg"][x]
            oxygen_max = json_data["data"]["oxygen"]["max"][x]
            oxygen_min = json_data["data"]["oxygen"]["min"][x]
            timeWindowStartTime = json_data["data"]["timeWindowStartTimes"][x]
            cur.execute('INSERT into vital_data (\
                    event_startTime,\
                    validSampleCount,\
                    firstReadingTime,\
                    heartRate_avg,\
                    heartRate_max,\
                    heartRate_min,\
                    lastReadingTime,\
                    movement_avg,\
                    oxygen_avg,\
                    oxygen_max,\
                    oxygen_min,\
                    timeWindowStartTime\
                )\
                    VALUES (\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?,\
                    ?\
                )\
                on conflict (event_startTime,timeWindowStartTime) do \
                UPDATE\
                SET\
                    event_startTime=?,\
                    validSampleCount=?,\
                    firstReadingTime=?,\
                    heartRate_avg=?,\
                    heartRate_max=?,\
                    heartRate_min=?,\
                    lastReadingTime=?,\
                    movement_avg=?,\
                    oxygen_avg=?,\
                    oxygen_max=?,\
                    oxygen_min=?,\
                    timeWindowStartTime=?\
                ',(event_startTime if event_startTime != "" else '',\
                   validSampleCount if validSampleCount != "" else '',\
                    firstReadingTime if firstReadingTime != "" else '',\
                    heartRate_avg if heartRate_avg != "" else '',\
                    heartRate_max if heartRate_max != "" else '',\
                    heartRate_min if heartRate_min != "" else '',\
                    lastReadingTime if lastReadingTime != "" else '',\
                    movement_avg if movement_avg != "" else '',\
                    oxygen_avg if oxygen_avg != "" else '',\
                    oxygen_max if oxygen_max != "" else '',\
                    oxygen_min if oxygen_min != "" else '',\
                    timeWindowStartTime if timeWindowStartTime != "" else '',\
                    \
                   event_startTime if event_startTime != "" else '',\
                   validSampleCount if validSampleCount != "" else '',\
                    firstReadingTime if firstReadingTime != "" else '',\
                    heartRate_avg if heartRate_avg != "" else '',\
                    heartRate_max if heartRate_max != "" else '',\
                    heartRate_min if heartRate_min != "" else '',\
                    lastReadingTime if lastReadingTime != "" else '',\
                    movement_avg if movement_avg != "" else '',\
                    oxygen_avg if oxygen_avg != "" else '',\
                    oxygen_max if oxygen_max != "" else '',\
                    oxygen_min if oxygen_min != "" else '',\
                    timeWindowStartTime if timeWindowStartTime != "" else '')
                )

    def save_everything_to_db(self, db_name = 'owlet.db'):
        con = sqlite3.connect(db_name)
        cur = con.cursor()

        #Setup isolation level for performance reasons
        con.isolation_level = None

        self.create_db_structure(con, cur)

        # Get/Update device info
        for device in self.get_devices():
            print("Saving device {} to DB".format(device.dsn))
            self.save_device_to_db(con, cur, device)
            device.update()
            
            #Turn logging on
            try:
                device.reactivate()
            except OwletTemporaryCommunicationException:
                continue

            print("Saving device {}'s current state to DB".format(device.dsn))
            for name, property in device.get_properties().items():
                #Save Current Property Info
                self.save_device_property_to_db(con, cur, property)
                if property.expanded == False:
                    #Save Historical Property Datapoints
                    print("Saving device {}'s historical state for {} to DB".format(device.dsn, name), end ="")
                    self.save_device_property_datapoints_to_db(con, cur, device.dsn, name)
                    print("")
        
        print("Save events (like low O2 Alarm) to DB")
        self.save_events_to_db(con, cur)

        print("Save sleeping events to DB")
        self.save_events_to_db(con, cur, "EVENT_TYPE_PROFILE_SLEEP")
        
        con.close()
