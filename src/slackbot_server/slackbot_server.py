import time
import hmac
import json
import hashlib
import uvicorn
import logging
import asyncio
from urllib.parse import parse_qs
from fastapi import FastAPI, Request

app = FastAPI()
logging.config.dictConfig(uvicorn.config.LOGGING_CONFIG)
logger = logging.getLogger('uvicorn')

params = {
    'signing_secret': None,
    'version_number': 'v0',
    'command_callback': None,
    'interaction_callback': None,
    'event_callback': None,
}

invalid_request = {'text': 'Invalid Request'}
no_signing_secret = 'SlackBot Server running without request validation!'


async def validate_request(headers, body):
    if not params['signing_secret']:
        logger.warning(no_signing_secret)
        return True

    current_timestamp = time.time()
    slack_signature = headers.get('X-Slack-Signature')
    slack_timestamp = headers.get('X-Slack-Request-Timestamp')

    if not slack_signature or not slack_timestamp:
        return False

    # Safety check
    if abs(current_timestamp - int(slack_timestamp)) > 60 * 5:
        return False

    signature = b':'.join(
        [
            params['version_number'].encode('ascii'),
            slack_timestamp.encode('ascii'),
            body,
        ]
    )

    hash_signature = hmac.new(
        params['signing_secret'].encode('ascii'), signature, hashlib.sha256
    ).hexdigest()

    hash_signature = '{}={}'.format(params['version_number'], hash_signature)
    if hash_signature == slack_signature:
        return True
    return False


@app.post('/command')
async def index(request: Request):
    headers = request.headers
    body = await request.body()
    if not headers or not body:
        return invalid_request
    payload = {
        k: next(iter(v)) for k, v in parse_qs(body.decode('utf-8')).items()
    }
    validation = await validate_request(headers, body)
    if not validation:
        return invalid_request

    response = {}
    callback = params['command_callback']
    if callback and callable(callback):
        response = await callback(payload, headers, body)

    return response


@app.post('/interaction')
async def index(request: Request):
    headers = request.headers
    body = await request.body()
    payload = json.loads(parse_qs(body.decode('utf-8')).get('payload')[0])

    response = {}
    callback = params['interaction_callback']
    if callback and callable(callback):
        response = await callback(payload, headers, body)

    return response


@app.post('/event')
async def index(request: Request):
    headers = request.headers
    body = await request.body()
    payload = json.loads(body.decode('utf-8'))

    response = {}
    callback = params['event_callback']
    if callback and callable(callback):
        response = await callback(payload, headers, body)

    return response


def run(
    signing_secret=None,
    version_number='v0',
    command_callback=None,
    interaction_callback=None,
    event_callback=None,
    host='0.0.0.0',
    port=8080,
    **kwargs
):

    params['signing_secret'] = signing_secret
    params['version_number'] = version_number
    params['command_callback'] = command_callback
    params['interaction_callback'] = interaction_callback
    params['event_callback'] = event_callback

    if not signing_secret:
        logger.warning(no_signing_secret)

    uvicorn_params = {
        'host': host,
        'port': port,
        'debug': False,
    }
    uvicorn_params.update(kwargs)
    uvicorn.run(app, **uvicorn_params)
