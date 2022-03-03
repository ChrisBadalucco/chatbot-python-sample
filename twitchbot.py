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


class TwitchBot(irc.bot.SingleServerIRCBot):
  '''
  From irc/client.py:

  class SimpleIRCClient:
    """A simple single-server IRC client class.

    This is an example of an object-oriented wrapper of the IRC
    framework.  A real IRC client can be made by subclassing this
    class and adding appropriate methods.

    The method on_join will be called when a "join" event is created
    (which is done when the server sends a JOIN messsage/command),
    on_privmsg will be called for "privmsg" events, and so on.  The
    handler methods get two arguments: the connection object (same as
    self.connection) and the event object.

    Functionally, any of the event names in `events.py` may be subscribed
    to by prefixing them with `on_`, and creating a function of that
    name in the child-class of `SimpleIRCClient`. When the event of
    `event_name` is received, the appropriately named method will be
    called (if it exists) by runtime class introspection.
  '''

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
    # self.connection.privmsg(self.channel, 'peace out cub scouts')
    print('ChrisBadaBot: on_part...')
    self.connection.part([self.channel], 'Peace out cub scouts!')

  def on_pubmsg(self, conn, event):
    print('ChrisBadaBot: on_pubmsg...')
    if event.arguments[0][:1] == '!':
      # If a chat message starts with an exclamation point, try to run it as a command
      cmd = event.arguments[0].split(' ')[0][1:]
      print('ChrisBadaBot: Received command: ' + cmd)
      self.execute(event, cmd)

  def execute(self, event, cmd):
    print('ChrisBadaBot: execute...')

    if cmd == "game":
      # Poll the API to get current game.
      response = self.twitch.get_channel()
      self.connection.privmsg(self.channel, f"{response['display_name']} is currently playing{response['game']}")

    elif cmd == "title":
      # Poll the API the get the current status of the stream
      response = self.twitch.get_channel()
      self.connection.privmsg(self.channel, f"{response['display_name']} channel title is currently {response['status']}")

    elif cmd == "raffle":
      # Provide basic information to viewers for specific commands
      message = "This is an example bot, replace this text with your raffle text."
      self.connection.privmsg(self.channel, message)

    elif cmd == "schedule":
      message = "This is an example bot, replace this text with your schedule text."
      self.connection.privmsg(self.channel, message)

    else:
      # The command was not recognized
      self.connection.privmsg(self.channel, f"Did not understand command: {cmd}")


def main():
  bot = TwitchBot()
  try:
    bot.start()
  except KeyboardInterrupt:
    bot.on_part(None, None)  # TODO not working
    print('ChrisBadaBot: We outtie!')


if __name__ == "__main__":
  main()
