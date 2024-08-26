#!/usr/bin/env python3
import os
import sys

import requests
from dotenv import load_dotenv

import check_door_access

load_dotenv()

BEARER_TOKEN = os.getenv("MANUAL_BEAR")
BASE_URL = os.getenv("BASE_URL")
DOORLIST_ENDPOINT = BASE_URL + 'rpc/GetDoorListStartingFromItem'

if not all([BEARER_TOKEN, BASE_URL]):
    print("Error: Missing one or more environment variables (BEARER_TOKEN, BASE_URL)")
    sys.exit(1)

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
    "startingItem": None,
    "orderBy": 0,
    "maxCount": 30,
    "returnRelations": {
        "$type": "Salto.Services.Web.Model.Dto.AccessPoints.Doors.DoorRelationSet",
        "Data": True
    },
    "filterCriteria": "",
    "isForward": True
}

response = requests.post(DOORLIST_ENDPOINT, headers=headers, json=payload, verify=False, timeout=10)

if response.status_code == 200:
    response_data = response.json()
    for item in response_data:
        print(f"{item.get('Name')}")
        check_door_access.check_door_access(item.get('Id'))
        print("-" * 50)
else:
    print(f"Request failed with status code {response.status_code}")
