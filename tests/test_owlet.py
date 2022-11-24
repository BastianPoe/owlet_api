#!/usr/bin/env python

import responses
import requests
import pytest
import time
import copy
from unittest.mock import Mock, patch
from freezegun import freeze_time

from owlet_api.owletapi import OwletAPI
from owlet_api.owlet import Owlet
from owlet_api.owletexceptions import OwletPermanentCommunicationException
from owlet_api.owletexceptions import OwletTemporaryCommunicationException
from owlet_api.owletexceptions import OwletNotInitializedException

LOGIN_PAYLOAD = {
    'access_token': 'test_access_token',
    'idToken': 'test_id_token',
    'refreshToken': 'test_refresh_token',
    'refresh_token': 'test_refresh_token',
    'mini_token': 'test_min_token',
    'expiresIn': '3600',
    'expires_in': 86400
}

DEVICE_PAYLOAD = {
        'product_name': 'a', 
        'model': 'b', 
        'dsn': 'c', 
        'oem_model': 'd', 
        'sw_version': 'e', 
        'template_id': 1, 
        'mac': 'g', 
        'unique_hardware_id': None, 
        'hwsig': 'h', 
        'lan_ip': 'i', 
        'connected_at': 'j', 
        'key': 1, 
        'lan_enabled': False, 
        'has_properties': True, 
        'product_class': None, 
        'connection_status': 'k', 
        'lat': '1.0', 
        'lng': '2.0', 
        'locality': 'l', 
        'device_type': 'm'
}

DEVICE_ATTRIBUTES = [  
    {  
        'property':{  
            'type':'Property',
            'name':'AGE_MONTHS_OLD',
            'base_type':'integer',
            'read_only':False,
            'direction':'input',
            'scope':'user',
            'data_updated_at':'2018-12-30T09:43:23Z',
            'key':42738116,
            'device_key':24826059,
            'product_name':'Owlet Baby Monitors',
            'track_only_changes':True,
            'display_name':'Age (Months)',
            'host_sw_version':False,
            'time_series':False,
            'derived':False,
            'app_type':None,
            'recipe':None,
            'value':None,
            'denied_roles':[  
            ],
            'ack_enabled':False,
            'retention_days':30
        }
    },
    {  
        'property':{  
            'type':'Property',
            'name':'ALRTS_DISABLED',
            'base_type':'boolean',
            'read_only':False,
            'direction':'input',
            'scope':'user',
            'data_updated_at':'2018-12-30T09:43:23Z',
            'key':42738165,
            'device_key':24826059,
            'product_name':'Owlet Baby Monitors',
            'track_only_changes':True,
            'display_name':'Disable Alerts',
            'host_sw_version':False,
            'time_series':False,
            'derived':False,
            'app_type':None,
            'recipe':None,
            'value':None,
            'denied_roles':[  
            ],
            'ack_enabled':False,
            'retention_days':30
        }
    },{  
        'property':{  
            'type':'Property',
            'name':'APP_ACTIVE',
            'base_type':'boolean',
            'read_only':False,
            'direction':'input',
            'scope':'user',
            'data_updated_at':'2018-12-30T09:43:23Z',
            'key':42738119,
            'device_key':24826059,
            'product_name':'Owlet Baby Monitors',
            'track_only_changes':False,
            'display_name':'App Active',
            'host_sw_version':False,
            'time_series':False,
            'derived':False,
            'app_type':None,
            'recipe':None,
            'value':0,
            'denied_roles':[  
            ],
            'ack_enabled':False,
            'retention_days':30,
            'ack_status':None,
            'ack_message':None,
            'acked_at':None
        }
    },{  
        'property':{  
            'type':'Property',
            'name':'LOGGED_DATA_CACHE',
            'base_type':'boolean',
            'read_only':False,
            'direction':'input',
            'scope':'user',
            'data_updated_at':'2018-12-30T09:43:23Z',
            'key':42738119,
            'device_key':24826059,
            'product_name':'Owlet Baby Monitors',
            'track_only_changes':False,
            'display_name':'App Active',
            'host_sw_version':False,
            'time_series':False,
            'derived':False,
            'app_type':None,
            'recipe':None,
            'value':'http://de.mo/file',
            'denied_roles':[  
            ],
            'ack_enabled':False,
            'retention_days':30,
            'ack_status':None,
            'ack_message':None,
            'acked_at':None
        }
    }
]

DOWNLOAD_DATA = {  
   'datapoint':{  
      'updated_at':'2018-05-09T10:41:00Z',
      'created_at':'2018-05-09T10:41:00Z',
      'echo':False,
      'closed':True,
      'metadata':{  

      },
      'value':OwletAPI.base_properties_url + 'devices/24826059/properties/LOGGED_DATA_CACHE/datapoints/76ce9810-5375-11e8-e7a5-6450803806ca.json',
      'created_at_from_device':None,
      'file':'https://ayla-device-field-production-1a2039d9.s3.amazonaws.com/X?AWSAccessKeyId=Y&Expires=1234&Signature=Z'
   }
}



@responses.activate
def test_owlet_ok():
    # Initialize OwletAPI
    api = OwletAPI()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)
 
    assert device.product_name == "a"
    assert device.model == "b"
    assert device.dsn == "c"
    assert device.sw_version == "e"
    assert device.mac == "g"
    assert device.hwsig == "h"
    assert device.lan_ip == "i"
    assert device.connected_at == "j"
    assert device.connection_status == "k"
    assert device.lat == 1.0
    assert device.lon == 2.0
    assert device.device_type == "m"
    # and so on and so forth
    
@responses.activate
def test_update_ok():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    # Owlet will pull the properties of this particular device
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)

    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()
    
    assert device.get_property('AGE_MONTHS_OLD').value == None
    assert device.get_property('ALRTS_DISABLED').value == None
    assert device.get_property('APP_ACTIVE').value == 0

@responses.activate
def test_update_no_response():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)

    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()

    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.update()
    
    assert 'Server Request failed - no response' in str(info.value) 


@responses.activate
def test_update_return_code():
    # Owlet will pull the properties of this particular device
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=500)
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)

    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.update()
    
    assert 'Server Request failed - status code' in str(info.value) 


@responses.activate
def test_update_invalid_json():
    # Owlet will pull the properties of this particular device
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              body="INVALID", status=200)

    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)

    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.update()
    
    assert 'Update failed - JSON error' in str(info.value)


@responses.activate
def test_update_repeat():
    my_device_attributes = copy.deepcopy(DEVICE_ATTRIBUTES)
    my_device_attributes[0]['property']['value'] = 'DEADBEEF'
    my_device_attributes[0]['property']['data_updated_at'] = '2018-12-30T09:43:28Z'
    
    # Owlet will pull the properties of this particular device
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=my_device_attributes, status=200)
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)

    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    device.update()

    assert device.get_property('AGE_MONTHS_OLD').value == 'DEADBEEF'
    assert device.get_property('DOES_NOT_EXIST') == None
    
    properties = device.get_properties()
    assert properties['AGE_MONTHS_OLD'].value == 'DEADBEEF'

    assert device.get_update_interval() == 5

@responses.activate
def test_reactivate_ok():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.POST, OwletAPI.base_properties_url + 'properties/42738119/datapoints',
              status=201)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    device.reactivate()

@responses.activate
def test_reactivate_fail_no_attributes():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)

    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    with pytest.raises(OwletNotInitializedException) as info:
        device.reactivate()
    
    assert 'Initialize first - no properties' in str(info.value)


@responses.activate
def test_reactivate_fail_wrong_attributes():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)

    my_device_attributes = copy.deepcopy(DEVICE_ATTRIBUTES)
    my_device_attributes[0]['property']['name'] = 'DEADBEEF1'
    my_device_attributes[1]['property']['name'] = 'DEADBEEF2'
    my_device_attributes[2]['property']['name'] = 'DEADBEEF3'
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=my_device_attributes, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletNotInitializedException) as info:
        device.reactivate()
    
    assert 'Initialize first - missing property' in str(info.value)

@responses.activate
def test_reactivate_fail_no_connection():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.reactivate()

    assert 'Server Request failed - no response' in str(info.value)

@responses.activate
def test_reactivate_fail_status_code():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.POST, OwletAPI.base_properties_url + 'properties/42738119/datapoints',
              status=500)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.reactivate()

    assert 'Server Request failed, return code' in str(info.value)

@responses.activate
def test_download_logged_data_ok():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, 'http://de.mo/file', 
              json=DOWNLOAD_DATA, status=200)
    responses.add(responses.GET, 'https://ayla-device-field-production-1a2039d9.s3.amazonaws.com/X?AWSAccessKeyId=Y&Expires=1234&Signature=Z', 
              status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    device.download_logged_data()
    

@responses.activate
def test_download_logged_data_fail_no_init():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)
    print(device)
    
    with pytest.raises(OwletNotInitializedException) as info:
        device.download_logged_data()
    
    assert 'Initialize first - no properties' in str(info.value) 

@responses.activate
def test_download_logged_data_fail_no_attribute():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    my_device_attributes = copy.deepcopy(DEVICE_ATTRIBUTES)
    my_device_attributes[0]['property']['name'] = 'DEADBEEF3'
    my_device_attributes[1]['property']['name'] = 'DEADBEEF3'
    my_device_attributes[2]['property']['name'] = 'DEADBEEF3'
    my_device_attributes[3]['property']['name'] = 'DEADBEEF3'
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=my_device_attributes, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletNotInitializedException) as info:
        device.download_logged_data()
    
    assert 'Initialize first - missing property' in str(info.value)

@responses.activate
def test_download_logged_data_fail_no_connection():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.download_logged_data()
        
    assert 'Server Request failed - no answer' in str(info.value)


@responses.activate
def test_download_logged_data_fail_status_code():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, 'http://de.mo/file', 
              json=DOWNLOAD_DATA, status=500)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.download_logged_data()
    
    assert 'Server Request failed - return code' in str(info.value)


@responses.activate
def test_download_logged_data_fail_invalid_json():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, 'http://de.mo/file', 
              body="INVALID", status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.download_logged_data()
    
    assert 'Request failed - JSON invalid' in str(info.value)


@responses.activate
def test_download_logged_data_fail_incomplete_json():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    my_download_data = copy.deepcopy(DOWNLOAD_DATA)
    my_download_data['datapoint'] = {}
    responses.add(responses.GET, 'http://de.mo/file', 
              json=my_download_data, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.download_logged_data()
    
    assert 'Request failed - JSON incomplete' in str(info.value)


@responses.activate
def test_download_logged_data_fail_no_download():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, 'http://de.mo/file', 
              json=DOWNLOAD_DATA, status=200)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.download_logged_data()
    
    assert 'Download Request failed - no answer' in str(info.value)


@responses.activate
def test_download_logged_data_fail_no_download_code():
    responses.add(responses.POST, OwletAPI.owlet_login_url + OwletAPI.google_API_key,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.owlet_login_token_provider_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, OwletAPI.base_user_url,
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, OwletAPI.base_properties_url + 'dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, 'http://de.mo/file', 
              json=DOWNLOAD_DATA, status=200)
    responses.add(responses.GET, 'https://ayla-device-field-production-1a2039d9.s3.amazonaws.com/X?AWSAccessKeyId=Y&Expires=1234&Signature=Z', 
              status=500)
 
    # Initialize OwletAPI
    api = OwletAPI("test@test.de", "moped")
    api.login()
    
    # Instantiate the device
    device = Owlet(api, DEVICE_PAYLOAD)

    # Update the device
    device.update()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        device.download_logged_data()
    
    assert 'Download Request failed - status code' in str(info.value)
