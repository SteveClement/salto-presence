#!/usr/bin/env python3
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("MANUAL_BEAR")
BASE_URL = os.getenv("BASE_URL")
DOOR_RELATION_ENDPOINT = BASE_URL + 'rpc/GetDoorUserRelationList'

if not all([BEARER_TOKEN, BASE_URL]):
    print("Error: Missing one or more environment variables (BEARER_TOKEN, BASE_URL)")
    sys.exit(1)


def check_door_access(door_id):
    """
    Check the door access for a given door ID.

    Args:
        door_id (str): The ID of the door to check access for.

    Returns:
        None

    Raises:
        None
    """
    # Rest of the code...
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en,en-GB;q=0.9,en-LU;q=0.8,fr-FR;q=0.7,fr;q=0.6,en-US;q=0.5',
        'Authorization': 'Bearer ' + BEARER_TOKEN,
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'DNT': '1',
        'Origin': BASE_URL,
        'Referer': BASE_URL + 'index.html',
        'UMO': '120',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    payload = {
        "doorId": door_id,
        "startingItem": None,
        "orderBy": 0,
        "maxCount": 51,
        "filterCriteria": "",
        "isForward": True
    }

    response = requests.post(DOOR_RELATION_ENDPOINT, headers=headers, json=payload, verify=False, timeout=10)

    if response.status_code == 200:
        response_data = response.json()
        for item in response_data:
            access_subject = item.get('AccessSubject')
            if access_subject:
                print(f"{access_subject.get('Name')},{item.get('CardholderTimetable').get('Name')}")
    else:
        print(f"Request failed with status code {response.status_code}")
