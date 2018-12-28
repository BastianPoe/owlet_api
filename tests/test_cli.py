#!/usr/bin/env python

import responses
import requests
import pytest
import time
import copy
import sys
from unittest.mock import Mock, patch
from freezegun import freeze_time

from owlet_api.owletapi import OwletAPI
from owlet_api.owlet import Owlet
from owlet_api.owletexceptions import OwletPermanentCommunicationException
from owlet_api.owletexceptions import OwletTemporaryCommunicationException
from owlet_api.owletexceptions import OwletNotInitializedException
from owlet_api.cli import cli

LOGIN_PAYLOAD = {
    'access_token': 'testtoken',
    'expires_in': 86400
}

DEVICES_PAYLOAD = [
    {
        'device':{
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
    }
]

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
      'value':'https://ads-field.aylanetworks.com/apiv1/devices/24826059/properties/LOGGED_DATA_CACHE/datapoints/76ce9810-5375-11e8-e7a5-6450803806ca.json',
      'created_at_from_device':None,
      'file':'https://ayla-device-field-production-1a2039d9.s3.amazonaws.com/X?AWSAccessKeyId=Y&Expires=1234&Signature=Z'
   }
}


@responses.activate
def test_cli_token():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', 'token']):
        cli()

@responses.activate
def test_cli_login_fail():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=401)
 

    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', 'token']):
        with pytest.raises(SystemExit) as info:
            cli()

        # Ensure exit code is 1 == error        
        assert '1' == str(info.value)

@responses.activate
def test_cli_server_down():
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', 'token']):
        with pytest.raises(SystemExit) as info:
            cli()

        # Ensure exit code is 1 == error        
        assert '1' == str(info.value)

@responses.activate
def test_cli_devices_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', 'devices']):
        cli()

@responses.activate
def test_cli_attributes_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', 'attributes']):
        cli()

@responses.activate
def test_cli_download_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.GET, 'http://de.mo/file', 
              json=DOWNLOAD_DATA, status=200)
    responses.add(responses.GET, 'https://ayla-device-field-production-1a2039d9.s3.amazonaws.com/X?AWSAccessKeyId=Y&Expires=1234&Signature=Z', 
              status=200)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', 'download']):
        cli()

#@pytest.mark.skip(reason="no way of currently testing this")
@responses.activate
def test_cli_stream_ok():

    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.POST, 'https://ads-field.aylanetworks.com/apiv1/properties/42738119/datapoints',
              status=201)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', '--timeout', '10', 'stream']):
        cli()

#@pytest.mark.skip(reason="no way of currently testing this")
@responses.activate
def test_cli_stream_updatefail():

    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.POST, 'https://ads-field.aylanetworks.com/apiv1/properties/42738119/datapoints',
              status=201)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=400)

    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', '--timeout', '10', 'stream']):
        cli()

#@pytest.mark.skip(reason="no way of currently testing this")
@responses.activate
def test_cli_stream_reactivationfail():

    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.POST, 'https://ads-field.aylanetworks.com/apiv1/properties/42738119/datapoints',
              status=400)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', '--timeout', '10', 'stream']):
        cli()

#@pytest.mark.skip(reason="no way of currently testing this")
@responses.activate
@patch('time.sleep')
def test_cli_stream_ctrlc(sleep_mock):
    sleep_mock.side_effect = SystemExit

    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json',
              json=DEVICES_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/dsns/c/properties',
              json=DEVICE_ATTRIBUTES, status=200)
    responses.add(responses.POST, 'https://ads-field.aylanetworks.com/apiv1/properties/42738119/datapoints',
              status=201)
 
    with patch('sys.argv', ['cli.py', 'test@test.de', 'moped', '--timeout', '10', 'stream']):
        with pytest.raises(SystemExit):
            cli()

def test_cli_main():
    from owlet_api import cli
    
    with patch.object(cli, "cli", return_value=42):
        with patch.object(cli, "__name__", "__main__"):
            with patch.object(cli.sys, 'exit') as mock_exit:
                cli.init()
            
                assert mock_exit.call_args[0][0] == 42