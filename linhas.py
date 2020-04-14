from cache import cache
from geocode import geocode_reverse
import sys
import re
import math
import json
from lxml.html import fromstring as parse_html
from euclid import Vector3 as Vector
from datetime import timedelta
from functools import wraps
import asyncio
import aiohttp
import aiocache
import itertools

async def fetch_url(url):
    async with aiohttp.ClientSession() as aiohttp_session:
        async with aiohttp_session.get(url) as resp:
            return await resp.text()

def strip(x):
    return re.sub('[\\s\\xa0]+', ' ', x.strip())

def fix_route_name(route_short_name, route_long_name):
    return re.sub('^' + route_short_name + ' - ', '', route_long_name)

@aiocache.cached(cache=cache, ttl=timedelta(hours=1))
async def linhas():
    regex = '\\s*var v_item = "(\\d+)-[|]-(\\d+)-[|]-(.+)";'
    response = await fetch_url('http://www.emdec.com.br/ABusInf/consultarlinha.asp')
    ret = {}
    for line in response.splitlines():
        match = re.match(regex, line)
        if match:
            code = match.group(1)
            if match.group(2) != '0':
                code += '-' + match.group(2)
            ret[code] = fix_route_name(code, match.group(3))
    return ret

def parseMap(text):
    latlng_re = "new google.maps.LatLng\\(([.\\-\\d]+),( ?)([.\\-\\d]+)\\)"
    stop_re = "var pp_(\\d+) = " + latlng_re + ";"
    shapes_re = "var l_(\\d+) = \\[ ([^;]*) \\];"
    stops = [
        [float(x[1]), float(x[3])]
        for x in re.findall(stop_re, text)
    ]

    shapes = [
        [
            [float(x[0]), float(x[2])]
            for x in re.findall(latlng_re, shape[1])
        ]
        for shape in re.findall(shapes_re, text)
    ]
    return {
        "stops": stops,
        "shapes": shapes,
    }

EARTH_RADIUS = 6378100;
def latlng2vec(latlng):
    lat = math.radians(latlng[0])
    lng = math.radians(latlng[1])
    return Vector(
        math.cos(lat) * math.cos(lng),
        math.cos(lat) * math.sin(lng),
        math.sin(lat)
    )

def vec2latlng(vec):
    x = vec.x
    y = vec.y
    z = vec.z
    return [
        math.degrees(math.atan(z / math.sqrt(x*x + y*y))),
        math.degrees(math.atan2(y, x))
    ]
def dist_to_segment(A, B, C):
    offset = 3;  # até 3 metros de diferença, prefere ficar a direita do segmento
    # Assumes a planar triangle
    bc = abs(B-C);
    ac = abs(A-C);
    ab = abs(A-B);
    sign = B.cross(C).dot(A) >= 0;

    if (bc > ab) and (bc > ac):
        p = (ab+bc+ac)/2;
        h = (2/bc)*math.sqrt(p*(p-ab)*(p-bc)*(p-ac));
        bh = math.sqrt(ab*ab - h*h);
        ch = math.sqrt(ac*ac - h*h);
        frac = bh/(bh+ch);
        return {
            'distance': EARTH_RADIUS*h + (offset if sign else 0),
            'frac': frac,
            'nearest': B*(1-frac) + (C*frac),
            'sign':sign
        }
    elif ab < ac:
        return {
            'distance': EARTH_RADIUS*ab + (offset if sign else 0),
            'frac': 0,
            'nearest': B,
            'sign':sign
        }
    else:
        return {
            'distance': EARTH_RADIUS*ac + (offset if sign else 0),
            'frac': 1,
            'nearest': C,
            'sign':sign
        }


async def process_map(map):
    all_shapes = []
    all_stops = []
    for raw_shape in map['shapes']:
        shape = []
        all_shapes.append(shape)
        all_stops.append([])
        for latlng in raw_shape:
            vec = latlng2vec(latlng)
            shape_dist = 0
            if shape:
                shape_dist = shape[-1]['shape_dist'] + abs(shape[-1]['vec'] - vec) * EARTH_RADIUS
            #print('shape_dist=', shape_dist
            shape.append({
                'latlng': latlng,
                'vec': vec,
                'shape_dist': shape_dist
            })
    while len(all_shapes) < 2:
        all_shapes.append([])
        all_stops.append([])

    for latlng in map['stops']:
        vec = latlng2vec(latlng)
        nearest_segment = None
        for shape_index in range(len(all_shapes)):
            for segment_index in range(len(all_shapes[shape_index])-1):
                dist = dist_to_segment(vec, all_shapes[shape_index][segment_index]['vec'], all_shapes[shape_index][segment_index+1]['vec'])
                if nearest_segment is None or nearest_segment['distance'] > dist['distance']:
                    nearest_segment = dist
                    nearest_segment['shape_index'] = shape_index
                    nearest_segment['segment_index'] = segment_index
                    nearest_segment['shape_dist'] = \
                        all_shapes[shape_index][segment_index  ]['shape_dist']*(1-dist['frac']) + \
                        all_shapes[shape_index][segment_index+1]['shape_dist']*(  dist['frac'])
        all_stops[nearest_segment['shape_index']].append({
            'latlng': latlng,
            'nearest_latlng': vec2latlng(nearest_segment['nearest']),
            'shape_dist': nearest_segment['shape_dist']
        })

    #Add First and last points in shape if there are no stops withing 50m
    for (shape, stops) in zip(all_shapes, all_stops):
        stops.sort(key=lambda x: x['shape_dist'])
        if len(shape) >= 2:
            if len(stops) == 0 or abs(shape[0]['shape_dist'] - stops[0]['shape_dist']) > 50:
                stops.insert(0, {
                    'latlng': shape[0]['latlng'],
                    'nearest_latlng': shape[0]['latlng'],
                    'shape_dist': shape[0]['shape_dist']
                })
            if len(stops) == 0 or abs(shape[-1]['shape_dist'] - stops[-1]['shape_dist']) > 50:
                stops.insert(-1, {
                    'latlng': shape[-1]['latlng'],
                    'nearest_latlng': shape[-1]['latlng'],
                    'shape_dist': shape[-1]['shape_dist']
                })

    #print('Geocoding stop addresses...')
    async def populated_stop_name(stop):
        stop['name'] = await geocode_reverse(stop['latlng'])

    await asyncio.gather(*[
        populated_stop_name(stop)
        for stop in itertools.chain(*all_stops)
    ])

    #JSON-Friendly result
    return [
        {
            'shape': [
                {
                    'latlng': vertex['latlng'],
                    'shape_dist': vertex['shape_dist'],
                }
                for vertex in shape
            ],
            'stops': sorted(stops, key=lambda x: x['shape_dist'])
        }
        for (shape, stops) in zip(all_shapes, all_stops)
    ]
    return zip(map['shapes'], all_stops)




def get_text(dom, name):
    dom = dom.cssselect('input[name="%s"]' % name)
    if dom:
        v = dom[0].get("value")
        v = re.sub(r"\s+", " ", v)
        v = re.sub(r"^\s", "", v)
        v = re.sub(r"\s$", "", v)
        return v

@aiocache.cached(cache=cache, ttl=(timedelta(days=3), timedelta(days=7)))
async def detalhes(linha):
    linha_dash = linha if '-' in linha else linha + '-0'

    # Busca pelo numero da linha
    pag_query = await fetch_url(f'http://www.emdec.com.br/ABusInf/consultarlinha.asp?linha={linha_dash}&consulta=1')
    for line in pag_query.splitlines():
        pag_query_regex = '\\s*document.JnInformacoes.action = "detalhelinha.asp\\?(.*)";'
        match = re.match(pag_query_regex, line)
        if match:
            url_detalhes = f'http://www.emdec.com.br/ABusInf/detalhelinha.asp?{match.group(1)}'
            break

    pag_detalhes = parse_html(await fetch_url(url_detalhes))
    pag_map = await fetch_url(f'http://www.emdec.com.br/ABusInf/{pag_detalhes.cssselect("#mapFrame")[0].get("src")}')
    map_data = parseMap(pag_map)
    processed_map = await process_map(map_data)

    def schedules(dom):
        ret = {}
        for group in dom.xpath('div'):
            title_node = group.xpath('p')[-1]
            name = {
                u'Horários Sábado': 'saturday',
                u'Horários Sábado (Referência)': 'saturday',
                u'Horários Domingo': 'sunday',
                u'Horários Domingo (Referência)': 'sunday',
                u'Horários Útil': 'weekday',
                u'Horários Útil (Referência)': 'weekday',

            }[strip(title_node.text)]
            trips = []
            ret[name] = {
                'trips': trips,
                'vehicles': int(re.search('\\d+', title_node.tail).group())
            }
            #print(strip(group.xpath('p')[-1].tail))

            for cell in group.xpath('div/table/tr/td'):
                trips.append({
                    'time': strip(cell.xpath('table/tr/td')[0].text),
                    'wheelchair_accessible': bool(cell.xpath('table/tr/td/img'))
                })

        return ret


    def stops(dom):
        return [
            strip(td.text)
            for td in dom.cssselect('div > table > tr > td')
        ]

    def trecho(dom, map_data):
        details = {}
        for tr in dom.xpath('div/table/tr'):
            details[strip(tr.cssselect('td')[0].text)[:-1]] = tr.cssselect('td input')[0].get('value')

        main_panels = dom.xpath('table/tr/td')

        ret = {}
        ret["details"] = details
        #ret["end_location"] = geocode(details["Letreiro"])
        ret["schedules"] = schedules(main_panels[0])
        #ret["stops"] = stops(main_panels[1])
        ret["map"] = map_data
        return ret

    trechos = [
        trecho(div, processed_map[map_index])
        for (div, map_index) in zip(pag_detalhes.cssselect('#tabs > div'), [1,0])
    ]
    trechos = [trecho for trecho in trechos if trecho['map']['shape'] and trecho['details']['Letreiro'] != 'ESPECIAL']

    route_long_name = fix_route_name(linha, get_text(pag_detalhes, 'txtPesquisa').split(' - ', 1)[-1])

    ret = {}
    ret["route_short_name"] = linha
    ret["route_long_name"] = route_long_name
    ret["company"] = get_text(pag_detalhes, 'txtEmpresa')
    ret["comments"] = get_text(pag_detalhes, 'txtObservacao')
    ret["updated"] = strip(pag_detalhes.cssselect('#conteudo font[size="1"]')[0].text.split('\n')[1])
    ret["route_url"] = 'http://www.portalinterbuss.com.br/campinas/linhas/%s' % linha

    # http://www.portalinterbuss.com.br/campinas/layout-da-frota
    ret["route_color"] = {
        '1': '1985E9', # AZUL CLARO
        '2': 'e91919', # VERMELHO
        '3': '0D2447', # VERDE
        '4': '0D2447', # AZUL ESCURO
        '5': '9D9D9D', # BRANCO COM FIGURAS
    }[linha[0]]
    ret["route_text_color"] = {
        '1': 'C6E4FF', # AZUL CLARO
        '2': 'FFDDDD', # VERMELHO
        '3': 'E8FFDC', # VERDE
        '4': 'CFE2FF', # AZUL ESCURO
        '5': 'EFEFEF', # BRANCO COM FIGURAS
    }[linha[0]]
    ret["directions"] = trechos

    print(f"Fetched details from {linha}")
    return ret

async def main():
    routes = sys.argv[1:] or (await linhas()).keys()
    for i, linha in enumerate(routes):
        details = await detalhes(linha)
        print(f'{i+1}/{len(routes)}: {linha} - {details["route_long_name"]}')
        with open(f'out/{linha}.json', 'w') as f:
            f.write(json.dumps(details, indent=4))

if __name__ == "__main__":
    asyncio.run(main())

