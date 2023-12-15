import json
import math
import os
import requests
import time

from dotenv import load_dotenv
from munch import munchify
from prometheus_client import start_http_server, Gauge
from urllib.parse import urljoin

load_dotenv()
NODE_URL = os.getenv("NODE_URL")
NETWORK_ID = os.getenv("NETWORK_ID")
POLL_SECONDS = int(os.getenv("POLL_SECONDS"))
HTTP_PORT = int(os.getenv("HTTP_PORT"))

# Define a Gauge metric to track peggo event lag
ALEO_LATEST_HEIGHT = Gauge("aleo_latest_height", "the latest block height")


def request(url: str, endpoint: str):
    r = requests.get(f"{url}/{endpoint}")
    if r.status_code != 200:
        return math.nan
    return r.content


def process_request(node_url: str):
    latest_height = int(request(node_url, "latest/height"))
    ALEO_LATEST_HEIGHT.set(latest_height)

    peer_count = int(request(node_url, "peers/count"))
    ALEO_PEER_COUNT.set(peer_count)

    latest_block_response = json.loads(request(node_url, "latest/block"))
    if latest_block_response is math.nan:
        ALEO_COINBASE_TARGET.set(latest_block_response)
    else:
        munched = munchify(latest_block_response)
        metadata = munched.header.metadata

        ALEO_COINBASE_TARGET.set(int(metadata.coinbase_target))


def main():
    start_http_server(HTTP_PORT)

    node_url = urljoin(NODE_URL, NETWORK_ID)
    while True:
        process_request(node_url)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    print(f"Polling {NODE_URL} every {POLL_SECONDS} seconds")
    print(f"On port {HTTP_PORT}")

    main()
