#!/usr/bin/env python3
import requests


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Alt-Used': 'sports.bwin.com',
    'Connection': 'keep-alive',
    'Content-Length': '5117',
    'Content-type': 'application/json',
    'Host': 'sports.bwin.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0',
    'Origin': 'null',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'TE': 'trailers',
    'Upgrade-Insecure-Requests': '1',
}
r = requests.get('https://sports.bwin.com/en/api/clientconfig', headers=headers)
#  Figure out a way to stop getting a 403
assert r.status_code == 200
print(r.json())
dynamically_generated_access_id = ''
website = f'https://sports.bwin.com/cds-api/random-multi-generator/random-events?x-bwin-accessid={dynamically_generated_access_id}&lang=en&country=GB&userCountry=GB'
