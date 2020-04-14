from quart import Quart, redirect, jsonify, send_file
import linhas
import emdec2gtfs
import asyncio
import aiocache
from asyncio_pool import AioPool

app = Quart(__name__)
#app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

async def all_routes():
    return await linhas.linhas()

async def route_details(route_codes):
    async with AioPool(20) as fetch_pool:
        details = await fetch_pool.map(linhas.detalhes, route_codes)
        return dict(zip(route_codes, details))

async def parse_route_codes(route_codes):
    valid_route_codes = (await all_routes()).keys()
    if route_codes=='all':
        return 'all', valid_route_codes
    else:
        route_codes = sorted([
            route_code.strip()
            for route_code in route_codes.split(",")
            if route_code.strip()
        ])
        for route_code in route_codes:
            if route_code not in valid_route_codes:
                raise ValueError(f"Unknown route: {route_code}")
        return '_'.join(route_codes), route_codes


@app.route('/')
async def index():
   return redirect("https://github.com/paulo-raca/emdec-gtfs")

@app.route('/route/list')
async def route_list():
    return jsonify(await all_routes())

@app.route('/route/<route_codes>.json')
async def route_as_json(route_codes):
    name, route_codes = await parse_route_codes(route_codes)
    return jsonify(await route_details(route_codes))


@app.route('/route/<route_codes>.gtfs')
async def route_as_gtfs(route_codes):
    name, route_codes = await parse_route_codes(route_codes)
    details = await route_details(route_codes)
    gtfs = emdec2gtfs.build_gtfs(details).getzip()
    return await send_file(gtfs, mimetype='application/zip', as_attachment=True, attachment_filename=f"gtfs_{name}.zip")

if __name__ == "__main__":
    app.run()
