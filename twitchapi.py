import json
import os
import urllib
import webbrowser
from socket import socket
from typing import Literal

import requests
from requests import HTTPError

# https://dev.twitch.tv/docs/irc/guide for list of irc commands and required scopes
SCOPES = 'chat:edit chat:read whispers:edit whispers:read channel:moderate'
CLAIMS = ''
REDIRECT_URI = 'http://localhost:8337/redirect'


class TwitchAPI:
  def __init__(self):
    filepath = 'api-creds.json'
    if os.path.isfile(filepath):
      with open(filepath, 'r') as file:
        creds = json.load(file)
        client_id = creds['client_id']
        client_secret = creds['client_secret']
        last_user_token = creds['user_access_token'] or None
        last_app_token = creds['app_access_token'] or None

    self.client_id = client_id
    self.client_secret = client_secret
    self.user_token = self.get_valid_access_token(token_type='user', token=last_user_token)
    self.app_token = self.get_valid_access_token(token_type='app', token=last_app_token)
    self._save_credentials()

    filepath = 'hydra-creds.json'
    if os.path.isfile(filepath):
      with open(filepath, 'r') as file:
        hydra_creds = json.load(file)
        hydra_base_url = hydra_creds['url']
        hydra_server_api_key = hydra_creds['server_api_key']
        hydra_server_private_key = hydra_creds['server_private_key']

    self.hydra_base_url = hydra_base_url
    self.hydra_server_api_key = hydra_server_api_key
    self.hydra_server_private_key = hydra_server_private_key

  # TWITCH STUFF #

  def _get_twitch(self, url, headers=None, queryparams=None, app=False):
    headers = headers or {
      'Authorization': f'Bearer {self.app_token if app else self.user_token}',
      'Accept': 'application/json',
      'Client-ID': self.client_id
    }
    response = requests.get(url, headers=headers, params=queryparams)
    response.raise_for_status()
    return response.json()

  def _post_twitch(self, url, body=None, headers=None, queryparams=None):
    headers = headers or {'Accept': 'application/json'}
    response = requests.post(url, json=body, headers=headers, params=queryparams)
    response.raise_for_status()
    return response.json()

  def _save_credentials(self):
    creds = {
      'client_id': self.client_id,
      'client_secret': self.client_secret,
      'user_access_token': self.user_token,
      'app_access_token': self.app_token
    }
    with open("api-creds.json", "w") as f:
      f.write(json.dumps(creds))
    print("TwitchAPI: Credentials stored successfully.")

  def validate_token(self, token):
    bearer_token = f"Bearer {token}"
    return self._get_twitch(url="https://id.twitch.tv/oauth2/validate", headers={"Authorization": bearer_token})

  def get_valid_access_token(self, token_type: Literal['user', 'app'], token=None):
    if token:
      try:
        self.validate_token(token)
        print(f'TwitchAPI: {token_type.capitalize()} access token is valid.')
        return token
      except HTTPError:
        pass

    code = None
    if token_type == 'user':
      print('TwitchAPI: User token is invalid. Attempting to retrieve a new auth code.')
      code = self.get_auth_code()

    print(f"TwitchAPI: Attempting to retrieve a new {token_type} access_token.")
    token = self.get_access_token(token_type, code)
    return token

  def get_auth_code(self):
    auth_parms = {
      "redirect_uri": REDIRECT_URI,
      "client_id": self.client_id,
      "response_type": "code",
      "scope": SCOPES
    }
    webbrowser.open(f"https://id.twitch.tv/oauth2/authorize?{urllib.parse.urlencode(auth_parms)}")
    with socket() as s:
      s.bind(("127.0.0.1", 8337))
      s.listen()
      print("TwitchAPI: Waiting for request...")
      conn, addr = s.accept()
      with conn:
        print("TwitchAPI: Received a connection...")
        data = ""
        while True:
          currdata = conn.recv(1024)
          if not currdata:
            break
          print("TwitchAPI: Received: " + str(currdata.decode('utf-8')))
          data += str(currdata.decode('utf-8'))
          if data.endswith("\r\n\r\n"):  # means we are at the end of the header request
            break
        # we expect a browser to be requesting the root page, but all we really care about is the code which is included in the first line.
        # For more info, look into how HTTP works.
        firstline = data.splitlines()[0]
        start = firstline.find('?code=')
        start += 6
        end = start + 30
        code = firstline[start:end]
        # code = re.match(r"GET /\?code=(?P<code>.*)&scope=(?P<SCOPES>.*) HTTP/(?P<version>.*)", firstline).group("code")
        print(f"TwitchAPI: Received code {code} from browser!")
        content = "Thank you, code received".encode("utf-8")
        response = f"HTTP/1.1 200 OK\r\nHost: localhost\r\nServer: ChrisBadaBotTwitch/1.1\r\nContent-Type: text/plain\r\nContent-Length: {len(content)} \r\n\r\n"
        conn.sendall((response).encode("utf-8") + content)
      print("TwitchAPI: Connection closed.")
    print("TwitchAPI: Socket closed.")
    return code

  def get_access_token(self, token_type: Literal['user', 'app'], code=None):
    params = {
      "client_id": self.client_id,
      "client_secret": self.client_secret,
      "redirect_uri": REDIRECT_URI
    }

    if token_type == 'app':
      # getting an app access token
      params.update({"grant_type": "client_credentials"})
    elif token_type == 'user' and code is not None:
      # getting a user access token
      params.update({"grant_type": "authorization_code", "code": code})
    else:
      raise AttributeError('Could not determine the type of access token to request.', token_type, code)

    response = self._post_twitch("https://id.twitch.tv/oauth2/token", queryparams=params)
    print(f"TwitchAPI: Received {token_type} access_token {response['access_token']}")
    return response['access_token']

  def get_twitch_account(self, username):
    url = 'https://api.twitch.tv/helix/users'
    queryparams = {'login': username}
    response = self._get_twitch(url, queryparams=queryparams, app=True)
    print(f"TwitchAPI: Successfully retrieved Twitch account for {username}", response)
    return response

  def get_channel(self):
    url = 'https://api.twitch.tv/helix/channels/'
    return self._get_twitch(url)

  # HYDRA STUFF - (could probably get broken out to own class) #

  def _get_hydra(self, url, headers=None, queryparams=None):
    headers = headers or {
      'Accept': 'application/json',
      'x-hydra-api-key': self.hydra_server_api_key,
      'x-hydra-server-private-key': self.hydra_server_private_key
    }
    response = requests.get(url, headers=headers, params=queryparams)
    response.raise_for_status()
    return response.json()

  def get_hydra_version(self):
    return requests.get(url=f'{self.hydra_base_url}/health/version')

  def get_hydra_account(self, twitch_user_id):
    try:
      response = self._get_hydra(url=f"{self.hydra_base_url}/accounts/twitch/{twitch_user_id}")
      print(f"TwitchAPI: Successfully retrieved Hydra account for {twitch_user_id}.", response)
      return response
    except HTTPError as e:
      if e.response.status_code == 404:
        print(f"TwitchAPI: No Hydra account found for {twitch_user_id}.")
      else:
        print(f"TwitchAPI: Failed communicating to Hydra.")
      return

  def _put_hydra(self, url, body=None, headers=None, queryparams=None):
    headers = headers or {
      'Accept': 'application/json',
      'x-hydra-api-key': self.hydra_server_api_key,
      'x-hydra-server-private-key': self.hydra_server_private_key
    }
    response = requests.put(url, json=body, headers=headers, params=queryparams)
    response.raise_for_status()
    return response.json()

  def hydra_ban(self, hydra_account_id, reason=None, duration=1, units='minutes'):
    url = f"{self.hydra_base_url}/accounts/{hydra_account_id}/ban"
    body = {}
    if reason:
      body['data'] = {'reason': reason}
    if duration:
      body['duration'] = duration
      body['units'] = units
    try:
      self._put_hydra(url, body=body)
      print(f"TwitchAPI: Successfully banned Hydra account {hydra_account_id}")
    except HTTPError:
      # oh well, we tried
      print(f"TwitchAPI: Ban for Hydra account {hydra_account_id} failed due to an HTTP error.")

