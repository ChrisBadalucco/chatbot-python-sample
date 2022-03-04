'''
Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
'''
import json
import os
import random

import irc.bot

from twitchapi import TwitchAPI

SERVER = 'irc.chat.twitch.tv'
PORT = 6667
MOTDS = [
  'Safety First',
  'There is always money in the banana stand',
  'Accept who you are. Unless you are a serial killer.',
  'If a book about failures does not sell, is it a success?'
]
COLORS = [
  'Blue', 'Coral', 'DodgerBlue', 'SpringGreen', 'YellowGreen',
  'Green', 'OrangeRed', 'Red', 'GoldenRod', 'HotPink', 'CadetBlue',
  'SeaGreen', 'Chocolate', 'BlueViolet', 'Firebrick'
]


class TwitchBot(irc.bot.SingleServerIRCBot):

  def __init__(self):
    filepath = 'bot-creds.json'
    if os.path.isfile(filepath):
      with open(filepath, 'r') as file:
        creds = json.load(file)
        username = creds['username']
        channel = creds['channel']

    self.channel = f"#{channel}"

    self.twitch = TwitchAPI()

    # Create IRC bot connection
    print(f"ChrisBadaBot: Connecting to {SERVER} on port {PORT}...")
    irc.bot.SingleServerIRCBot.__init__(self, [(SERVER, PORT, f"oauth:{self.twitch.user_token}")], username, username)

  def on_welcome(self, conn, event):
    print(f"ChrisBadaBot: Joining {self.channel}")
    # You must request specific capabilities before you can use them
    conn.cap('REQ', ':twitch.tv/membership')
    conn.cap('REQ', ':twitch.tv/tags')
    conn.cap('REQ', ':twitch.tv/commands')
    conn.join(self.channel)
    self.connection.privmsg(self.channel, 'has entered the chat!')

  def on_motd(self, conn, event):
    print(f"ChrisBadaBot: on_motd...")
    self.connection.privmsg(self.channel, f'Message of the Day: {random.choice(MOTDS)}')

  def on_part(self, conn, event):
    print('ChrisBadaBot: on_part...')
    self.connection.part([self.channel], 'Peace out cub scouts!')

  def on_pubmsg(self, conn, event):
    print('ChrisBadaBot: on_pubmsg...')
    if event.arguments[0][:1] == '!':
      # If a chat message starts with an exclamation point, try to run it as a command
      cmd = event.arguments[0].split(' ')[0][1:]
      print(f'ChrisBadaBot: Received command: {cmd}')
      self.execute_command(event, cmd)

  def execute_command(self, event, cmd):
    print('ChrisBadaBot: execute_command...')

    if cmd == 'test':
      self.connection.privmsg(self.channel, 'Test PASSED with flying colors!')

    elif cmd == 'account':
      twitch_account = self.twitch.get_twitch_account(event.source.user)
      if twitch_account:
        self.connection.privmsg(self.channel, f"Your Username is '{twitch_account['data'][0]['display_name']}'... but you already knew that didn't you ;)")
      else:
        self.connection.privmsg(self.channel, "Whoops, something went wrong.")

    elif cmd == "hydra-account":
      user_id = self.get_user_id_from_event(event)
      hydra_account = self.twitch.get_hydra_account(user_id)
      if hydra_account:
        self.connection.privmsg(self.channel, f"Your Hydra Username is '{hydra_account['identity']['username']}'")
      else:
        self.connection.privmsg(self.channel, "Whoops, something went wrong.")

    elif cmd == 'praise-bot':
      # TODO inc profile.data.twitch_praise
      pass

    elif cmd == "game":
      response = self.twitch.get_channel()
      self.connection.privmsg(self.channel, f"{response['display_name']} is currently playing{response['game']}")

    elif cmd == "title":
      self.connection.privmsg(self.channel, "this uh, doesnt work yet")
      # TODO response = self.twitch.get_channel()
      #  self.connection.privmsg(self.channel, f"{response['display_name']} channel title is currently {response['status']}")

    elif cmd == "color":
      color = random.choice(COLORS)
      self.connection.privmsg(self.channel, f"/color {color}")
      self.connection.privmsg(self.channel, f"{event.source.user} asked me to change my color to {color}")

    elif cmd == "hydra-version":
      response = self.twitch.get_hydra_version()
      if response.status_code != 200:
        self.connection.privmsg(self.channel, 'Whoops, something went wrong. Try again later.')
        return

      response = response.json()
      self.connection.privmsg(self.channel, f"Hydra is currently on version {response['version']}")

    else:
      # The command was not recognized
      self.connection.privmsg(self.channel, f"{cmd} does not compute...")

  def get_user_id_from_event(self, event):
    user_id = [tag['value'] for tag in event.tags if tag['key'] == 'user-id'][0]  # there should only be one user-id tag
    print(f"ChrisBadaBot: Found Twitch UserID: {user_id}")
    return user_id


def main():
  bot = TwitchBot()
  try:
    bot.start()
  except KeyboardInterrupt:
    bot.on_part(None, None)  # TODO not working
    print('ChrisBadaBot: We outtie!')


if __name__ == "__main__":
  main()
