import aiocache
import aiohttp
from cache import cache
from datetime import timedelta
import random
import re

# Each API Key can only do 2.5k requests/day
# Emdec DB has ~5k stops, therefore we need to spread requests on multiple keys :/
GEOCODER_API_KEYS = []
with open("geocode_keys.txt", "r") as f:
    for line in  f:
        line = re.sub("#.*", "", line).strip()
        if (line):
            GEOCODER_API_KEYS.append(line)
print("GEOCODER_API_KEYS:", GEOCODER_API_KEYS)
if not GEOCODER_API_KEYS:
    print("==== NO Keys were specified in geocode_keys.txt, geocoding will be disabled")


@aiocache.cached(cache=cache, ttl=(timedelta(days=25), timedelta(days=35)))
async def geocode_reverse(point):
    if not GEOCODER_API_KEYS:
        return f"{point[0]},{point[1]}"

    key = random.choice(GEOCODER_API_KEYS)
    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={point[0]},{point[1]}&key={key}'
    async with aiohttp.ClientSession() as aiohttp_session:
        async with aiohttp_session.get(url) as resp:
            data = await resp.json()
    address = data["results"][0]["formatted_address"]
    return re.sub(', Campinas.*', '',  address)
