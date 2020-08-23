#!/usr/bin/env python

import responses
import requests
import pytest
import time
import copy
from unittest.mock import MagicMock, Mock, patch
from freezegun import freeze_time

from owlet_api.owletapi import OwletAPI, OwletRegion
from owlet_api.owlet import Owlet
from owlet_api.owletexceptions import OwletPermanentCommunicationException
from owlet_api.owletexceptions import OwletTemporaryCommunicationException
from owlet_api.owletexceptions import OwletNotInitializedException

JWT_PAYLOAD = {
    'idToken': 'mytoken',
}

MINI_TOKEN_PAYLOAD = {
    'mini_token': 'mini_token',
}

LOGIN_PAYLOAD = {
    'access_token': 'testtoken',
    'expires_in': 86400
}

LOGIN_PAYLOAD2 = {
    'access_token': 'testtoken2',
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
def test_get_login_jwt_ok():
    responses.add(responses.POST, 'https://www.googleapis.com/identitytoolkit/v3/' + \
            'relyingparty/verifyPassword',
              json=JWT_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    jwt = api.get_login_jwt()

    assert jwt == "mytoken"

@responses.activate
def test_get_login_jwt_wrong_password():
    responses.add(responses.POST, 
            'https://www.googleapis.com/identitytoolkit/v3/' + \
                    'relyingparty/verifyPassword',
            status=401)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)

    with pytest.raises(OwletPermanentCommunicationException) as info:
        jwt = api.get_login_jwt()

    assert 'Login failed, check username and password' in str(info.value)


@responses.activate
def test_get_login_jwt_no_json():
    responses.add(responses.POST, 
            'https://www.googleapis.com/identitytoolkit/v3/' + \
                    'relyingparty/verifyPassword',
              status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        jwt = api.get_login_jwt()

    assert 'Server did not supply valid json, try again' in str(info.value)


@responses.activate
def test_get_login_jwt_no_token():
    responses.add(responses.POST, 
            'https://www.googleapis.com/identitytoolkit/v3/' + \
                    'relyingparty/verifyPassword',
              json={}, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        jwt = api.get_login_jwt()

    assert 'Server did not supply idToken, try again' in str(info.value)


@responses.activate
def test_get_login_mini_token_ok():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owletdata_signin'],
              json=MINI_TOKEN_PAYLOAD, status=200)

    token = api.get_login_mini_token('jwt')

    assert token == 'mini_token'


@responses.activate
def test_get_login_mini_token_no_json():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owletdata_signin'],
              status=200)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        token = api.get_login_mini_token('jwt')

    assert 'Server did not supply valid json, try again' in str(info.value)


@responses.activate
def test_get_login_mini_token_no_token():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owletdata_signin'],
              json={}, status=200)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        token = api.get_login_mini_token('jwt')
    
    assert 'Server did not supply mini_token, try again' in str(info.value)


@responses.activate
def test_login_ok():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
              json=LOGIN_PAYLOAD, status=200)

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
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)

    api.get_login_jwt = MagicMock(return_value="jwt", side_effect=OwletPermanentCommunicationException('Login failed, check username and password'))

    with pytest.raises(OwletPermanentCommunicationException) as info:
        api.login()
    
    assert 'Login failed, check username and password' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
    

@responses.activate
def test_login_fail_temporary():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)

    api.get_login_jwt = MagicMock(return_value="jwt", side_effect=OwletTemporaryCommunicationException('Server did not supply valid json, try again'))
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Server did not supply valid json, try again' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@responses.activate
def test_login_fail_invalidjson():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            status=200)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
        
    assert 'Server did not send valid json' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@responses.activate
def test_login_fail_incompletejson():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json={}, status=200)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Server did not send access token' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@pytest.mark.skip(reason="test needs to be fixed")
@responses.activate
def test_login_fail_noconnection():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
    
    assert 'Login request failed - no response' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None


@responses.activate
def test_get_auth_token_relogin():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD2, status=200)

    # Login happens at 2018-12-30 and lasts 1 day
    with freeze_time("2018-12-30"):
        api.login()
        assert api.get_auth_token() == "testtoken"

    with freeze_time("2019-12-30"):
        assert api.get_auth_token() == "testtoken2"


def test_get_auth_token_fail():
    api = OwletAPI()
    assert api.get_auth_token() == None


@responses.activate
def test_get_request_headers_ok():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)
    
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
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)

    api.login()

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owlet_properties'] + 'devices.json', json=DEVICES_PAYLOAD, status=200)
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
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)

    api.login()

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owlet_properties'] + 'devices.json', json=DEVICES_PAYLOAD, status=500)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.update_devices()
    
    assert 'Server request failed - status code' in str(info.value)

@responses.activate
def test_update_devices_fail_noresponse():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)

    api.login()

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.update_devices()
    
    assert 'Server request failed - no response' in str(info.value)

@responses.activate
def test_update_devices_fail_invalidjson():
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)

    api.login()

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owlet_properties'] + 'devices.json', status=200)

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
    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.set_region(OwletRegion.US)
    
    api.get_login_jwt = MagicMock(return_value="jwt")
    api.get_login_mini_token = MagicMock(return_value="mini_token")
    responses.add(responses.POST, api.get_config(OwletRegion.US)['owlet_signin'],
            json=LOGIN_PAYLOAD, status=200)

    api.login()

    responses.add(responses.GET, api.get_config(OwletRegion.US)['owlet_properties'] + 'devices.json', json=DEVICES_PAYLOAD, status=200)
    api.get_devices()
 
    assert api.get_update_interval() == 177
