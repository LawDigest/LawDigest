import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.environ.get("APIKEY_billProposers") or os.environ.get("APIKEY_lawmakers") or os.environ.get("APIKEY_billsInfo")
url = 'https://open.assembly.go.kr/portal/openapi/BILLINFOPPSR'

params = {
    'KEY': api_key,
    'Type': 'json',
    'pIndex': 1,
    'pSize': 100,
    # 'BILL_ID': 'PRC_U2Q4P0N2I2H6G1N0M1L9K3S2R4P1O4' 
    'BILL_ID': 'PRC_C2K4I0H4G1O6N1O0M3L3O3N3M5K6T2'
}

print(f"Requesting data for Bill ID: {params['BILL_ID']}")
response = requests.get(url, params=params)

if response.status_code == 200:
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)
else:
    print(f"Error: {response.status_code}")
