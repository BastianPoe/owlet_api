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
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()
    # If no exception occurred, everything seems to be fine
    
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == "test_access_token"
    assert api._expiry_time > time.time() + 86400 - 1
    assert api._expiry_time < time.time() + 86400 + 1
    assert api.get_auth_token() == "test_access_token"


@responses.activate
def test_login_fail():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=400)

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
def test_login_fail_step_1_api_key_bad():
    login_payload = {
        "error": {
            "details": [
                {
                    "reason": "API_KEY_INVALID",
                }
            ]
        }
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=login_payload, status=400)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletPermanentCommunicationException) as info:
        api.login()
    
    assert 'Login failed, bad API key.' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
 
@responses.activate
def test_login_fail_step_1_username_bad():
    login_payload = {
        "error": {
            "details": [
                {
                    "reason": "EMAIL_NOT_FOUND"
                }
            ]
        }
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=login_payload, status=400)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletPermanentCommunicationException) as info:
        api.login()
    
    assert 'Login failed, bad username' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
 
@responses.activate
def test_login_fail_step_1_password_bad():
    login_payload = {
        "error": {
            "details": [
                {
                    "reason": "INVALID_PASSWORD"
                }
            ]
        }
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=login_payload, status=400)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletPermanentCommunicationException) as info:
        api.login()
    
    assert 'Login failed, bad password' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_1_temporary():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
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
def test_login_fail_step_1_invalidjson():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              body="broken", status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
        
    assert 'Server did not send valid json (Step 1 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_1_incompletejson():
    login_payload = {
        'access_token': 'testtoken'
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=login_payload, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Server did not send id token (Step 1 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
      
@responses.activate
def test_login_fail_step_1_noconnection():
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
def test_login_fail_step_2_temporary():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=500)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Login request failed - status code (500) - (Step 2 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_2_invalidjson():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              body="broken", status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
        
    assert 'Server did not send valid json (Step 2 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_2_incompletejson():
    login_payload = {
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=login_payload, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Server did not send mini token (Step 2 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
      
@responses.activate
def test_login_fail_step_2_noconnection():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
            json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
    
    assert 'Login request failed - no response (Step 2 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_3_temporary():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=500)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Login request failed - status code (500) - (Step 3 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_3_app_id_or_app_secret_bad():
    login_payload = {
        'error': 'Could not find application'
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=login_payload, status=404)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletPermanentCommunicationException) as info:
        api.login()

    assert 'login request failed - app_id or app_secret is bad (Step 3 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_3_invalidjson():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              body="broken", status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
        
    assert 'Server did not send valid json (Step 3 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_login_fail_step_3_incompletejson():
    login_payload = {
        'access_token': 'testtoken'
    }
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=login_payload, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()

    assert 'Server did not send access token (Step 3 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None
      
@responses.activate
def test_login_fail_step_3_noconnection():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    
    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.login()
    
    assert 'Login request failed - no response (Step 3 of 3)' in str(info.value)
    assert api._email == "test@test.de"
    assert api._password == "moped"
    assert api._auth_token == None
    assert api.get_auth_token() == None

@responses.activate
def test_get_auth_token_ok():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()
    # If no exception occurred, everything seems to be fine
    
    assert api.get_auth_token() == "test_access_token"


@responses.activate
def test_get_auth_token_relogin():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    login_payload2 = copy.deepcopy(LOGIN_PAYLOAD)
    login_payload2['access_token'] = 'newtoken'
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=login_payload2, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=login_payload2, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=login_payload2, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")

    # Login happens at 2018-12-30 and lasts 1 day
    with freeze_time("2018-12-30"):
        api.login()
        assert api.get_auth_token() == "test_access_token"

        
    with freeze_time("2019-12-30"):
        assert api.get_auth_token() == "newtoken"


def test_get_auth_token_fail():
    api = OwletAPI()
    assert api.get_auth_token() == None


@responses.activate
def test_get_request_headers_ok():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    assert api.get_request_headers()['Content-Type'] == "application/json"
    assert api.get_request_headers()['Accept'] == "application/json"
    assert api.get_request_headers()['Authorization'] == "test_access_token"


def test_get_request_headers_fail():
    api = OwletAPI()

    assert api.get_request_headers() == None

@patch('owlet_api.owletapi.Owlet.__init__', Mock(return_value=None))
@responses.activate
def test_get_devices_ok():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-owlue1.aylanetworks.com/apiv1/devices.json', json=DEVICES_PAYLOAD, status=200)
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
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-owlue1.aylanetworks.com/apiv1/devices.json', json=DEVICES_PAYLOAD, status=500)

    with pytest.raises(OwletTemporaryCommunicationException) as info:
        api.update_devices()
    
    assert 'Server request failed - status code' in str(info.value)

@responses.activate
def test_update_devices_fail_noresponse():
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
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
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-owlue1.aylanetworks.com/apiv1/devices.json', body="invalid", status=200)

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
    responses.add(responses.POST, 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCBJ_5TRcPz_cQA4Xdqpcuo9PE5lR8Cc7k',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.GET, 'https://ayla-sso.owletdata.com/mini/',
              json=LOGIN_PAYLOAD, status=200)
    responses.add(responses.POST, 'https://ads-owlue1.aylanetworks.com/api/v1/token_sign_in.json',
              json=LOGIN_PAYLOAD, status=200)

    api = OwletAPI()
    api.set_email("test@test.de")
    api.set_password("moped")
    api.login()

    responses.add(responses.GET, 'https://ads-owlue1.aylanetworks.com/apiv1/devices.json', json=DEVICES_PAYLOAD, status=200)
    api.get_devices()
 
    assert api.get_update_interval() == 177
