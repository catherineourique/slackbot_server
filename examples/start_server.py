import os
import slackbot_server

server = slackbot_server.run(
    signing_secret = os.getenv('slackbot_signing_secret'),
    port = os.getenv('slackbot_port')
)
