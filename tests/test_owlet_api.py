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
    'access_token': 'testtoken',
    'expires_in': 86400
}

DEVICES_PAYLOAD = [
    {
        'device': 
            {
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

@responses.activate
def test_login_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()
    # If no exception occurred, everything seems to be fine
    
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == "testtoken"
    assert api._expiry_time > time.time() + 86400 - 1
    assert api._expiry_time < time.time() + 86400 + 1
    assert api.get_auth_token() == "testtoken"


@responses.activate
def test_login_fail():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=401)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletPermanentCommunicationException) as info:
        api.login()
    
    assert 'Login failed, check username and password' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
    

@responses.activate
def test_login_fail_temporary():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=500)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Login request failed - status code' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@responses.activate
def test_login_fail_invalidjson():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              body="broken", status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
        
    assert 'Server did not send valid json' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@responses.activate
def test_login_fail_incompletejson():
    login_payload = {
        'access_token': 'testtoken'
    }
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=login_payload, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Server did not send access token' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

      
@responses.activate
def test_login_fail_noconnection():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
    
    assert 'Login request failed - no response' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@responses.activate
def test_get_auth_token_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()
    # If no exception occurred, everything seems to be fine
    
    assert api.get_auth_token() == "testtoken"


@responses.activate
def test_get_auth_token_relogin():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    login_payload2 = copy.deepcopy(LOGIN_PAYLOAD)
    login_payload2['access_token'] = 'newtoken'
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=login_payload2, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")

    # Login happens at 2018-12-30 and lasts 1 day
    with freeze_time("2018-12-30"):
        api.login()
        assert api.get_auth_token() == "testtoken"

        
    with freeze_time("2019-12-30"):
        assert api.get_auth_token() == "newtoken"


def test_get_auth_token_fail():
    api = OwletAPI()
    assert api.get_auth_token() == None


@responses.activate
def test_get_request_headers_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    assert api.get_request_headers()['Content-Type'] == "application/json"
    assert api.get_request_headers()['Accept'] == "application/json"
    assert api.get_request_headers()['Authorization'] == "testtoken"


def test_get_request_headers_fail():
    api = OwletAPI()

    assert api.get_request_headers() == None

@patch('owlet_api.owletapi.Owlet.__init__', Mock(return_value=None))
@responses.activate
def test_get_devices_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json', json=DEVICES_PAYLOAD, status=200)
    api.get_devices()
    
    assert Owlet.__init__.called_once
    
    # Check if Owlet has been properly called
    args, kwargs = Owlet.__init__.call_args
    instance, arguments = args
    assert instance is api
    assert arguments == devices_payload[0]['device']
    
    # When calling get_devices again, no new instances of Owlet should be created
    api.get_devices()
    assert Owlet.__init__.called_once

@responses.activate
def test_update_devices_fail_servererror():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json', json=DEVICES_PAYLOAD, status=500)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.update_devices()
    
    assert 'Server request failed - status code' in str(info.value)

@responses.activate
def test_update_devices_fail_noresponse():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.update_devices()
    
    assert 'Server request failed - no response' in str(info.value)

@responses.activate
def test_update_devices_fail_invalidjson():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json', body="invalid", status=200)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.update_devices()
        
    assert 'Server did not send valid json' in str(info.value)

def test_update_devices_fail_noinit():
    api = OwletAPI()

    with pytest.raises(OwletNotInitializedException) as info:
        api.update_devices()
    
    assert 'Please login first' in str(info.value)

@patch('owlet_api.owletapi.Owlet.__init__', Mock(return_value=None))
@patch('owlet_api.owlet.Owlet.get_update_interval', Mock(return_value=177))
@responses.activate
def test_get_devices_ok():
    responses.add(responses.POST, 'https://user-field.aylanetworks.com/users/sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-field.aylanetworks.com/apiv1/devices.json', json=DEVICES_PAYLOAD, status=200)
    api.get_devices()
 
    assert api.get_update_interval() == 177
