import os
import slackbot_server

def command_callback(payload, headers, body):
    print('command')
    print(payload)

def interaction_callback(payload, headers, body):
    print('interaction')
    print(payload)
    
def event_callback(payload, headers, body):
    print('event')
    print(payload)


server = slackbot_server.run(
    signing_secret = os.getenv('slackbot_signing_secret'),
    port = os.getenv('slackbot_port')
    command_callback = command_callback,
    interaction_callback = interaction_callback,
    event_callback = event_callback,
)
