## HACKATHON MARCH 2022 NOTES

### Goals:
1. Connect to a Twitch channel chat via IRC
2. Code up a basic chat bot and get it working against my Twitch channel.
3. Setup proper auth flows for the chat bot.

Stretch Goals:
4. See if I can integrate with Hydra (grant a player an item?)
5. Deploy it to the cloud?
----------------------------------------
### How far I got:
1. Twitch Chat via IRC
    * IRC is the backbone for Twitch bots
    * Can also be used as an alternative to the web interface for normal chat
      * Demo twitch user interacting with twitch channel chat via IRC client


2. ChrisBadaBot - my chat bot

    * Basic IRC events
      * on_welcome
      * on_MOTD
      * on_public_message
        
    * Simple chat-only commands:
      * `!test` 
      * `!color`

    
3. Auth flows for Twitch API access

    * App Access Token
    * User Access Token

      * `!account` - get twitch account via API
        

4. Hydra Integration

    * Started with basics
      * `!hydra-version` - output the current version on QA

    * Added Server API Key
      * `!hydra-account` - returns the requesting user's Hydra username (full account in logs)
              * check every incoming message for "bad words" and temp ban the twitch user's Hydra account
