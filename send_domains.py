import sys
import requests
import os

API_BASE = os.getenv("DATAHUB_APIBASE")
TOKEN=os.getenv("DATAHUB_TOKEN")

domains = []

with open(sys.argv[1]) as fp:
    for l in fp:
        l = l.strip()
        if len(l) == 0:
            continue
        domains.append(l)
        if len(domains) >= 1000:
            print("sending ", domains[0], "...", domains[-1], end="\r")
            assert(requests.post(API_BASE+"v1/domains/add", headers={"Authorization": "Bearer "+TOKEN}, json=domains).status_code == 201)
            domains = []

if len(domains):
    assert(requests.post(API_BASE+"v1/domains/add", headers={"Authorization": "Bearer "+TOKEN}, json=domains).status_code == 201)
