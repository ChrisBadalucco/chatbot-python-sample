import json
import os
import re
import urllib
import webbrowser
from socket import socket
from typing import Literal

import requests
from requests import HTTPError

SCOPES = 'chat:edit chat:read whispers:edit whispers:read'
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

  def _get(self, url, headers=None, queryparams=None):
    headers = headers or {
      # TODO - we should be smarter about whether to default app or user access token... or refactor entirely
      'Authorization': f'Bearer {self.user_token}',
      'Accept': 'application/json',
      'Client-ID': self.client_id
    }
    response = requests.get(url, headers=headers, params=queryparams)
    response.raise_for_status()
    return response.json()

  def _post(self, url, body=None, headers=None, queryparams=None):
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
    return self._get(url="https://id.twitch.tv/oauth2/validate", headers={"Authorization": bearer_token})

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

    response = self._post("https://id.twitch.tv/oauth2/token", queryparams=params)
    print(f"TwitchAPI: Received {token_type} access_token {response['access_token']}")
    return response['access_token']

  def get_channel(self):
    url = 'https://api.twitch.tv/helix/channels/'
    return self._get(url)
