from __future__ import print_function

import re
import json
from lxml import etree
from lxml.html import fromstring as parse_html
from collections import OrderedDict

#import shelve
import urllib

url_cache = {} #shelve.open('emdec.db')
def fetch_url(url):
    url = str(url)

    if url in url_cache:
        ret = url_cache[url]
    else:
        print('fetching %s...' % url)
        req = urllib.urlopen(url)
        encoding = req.headers['content-type'].split('charset=')[-1]
        ret = unicode(req.read(), encoding)
        url_cache[url] = ret
        print('Done!')
    return ret

def strip(x):
    return re.sub('[\\s\\xa0]+', ' ', x.strip())


def xmlprint(*dom):
    for x in dom:
        print('vvvvvvvvvvvvvvvvvv')
        print(etree.tostring(x, pretty_print=True))
        print('^^^^^^^^^^^^^^^^^^')

def linhas():
    regex = '\\s*var v_item = "(\\d+)-[|]-(\\d+)-[|]-(.+)";'
    response = fetch_url('http://www.emdec.com.br/ABusInf/consultarlinha.asp')
    ret = OrderedDict()
    for line in response.splitlines():
        match = re.match(regex, line)
        if match:
            code = match.group(1)
            if match.group(2) != '0':
                code += '-' + match.group(2)
            ret[code] = match.group(3)
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

def get_text(dom, name):
    dom = dom.cssselect('input[name="%s"]' % name)
    if dom:
        return dom[0].get("value")

def detalhes(linha):
    if '-' not in linha:
        linha += '-0'
    # Busca pelo numero da linha
    pag_query_regex = '\\s*document.JnInformacoes.action = "detalhelinha.asp\\?(.*)";'
    pag_query = fetch_url(
        'http://www.emdec.com.br/ABusInf/consultarlinha.asp?linha=%s&consulta=1' % linha)
    for line in pag_query.splitlines():
        match = re.match(pag_query_regex, line)
        if match:
            url_detalhes = 'http://www.emdec.com.br/ABusInf/detalhelinha.asp?%s' % match.group(1)
            break

    pag_detalhes = parse_html(fetch_url(url_detalhes))
    pag_map = fetch_url('http://www.emdec.com.br/ABusInf/%s' % pag_detalhes.cssselect('#mapFrame')[0].get('src'))

    def schedules(dom):
        ret = OrderedDict()
        for group in dom.xpath('div'):
            name = strip(group.xpath('p')[-1].text)
            times = OrderedDict()
            ret[name] = times

            for cell in group.xpath('div/table/tr/td'):
                time = strip(cell.xpath('table/tr/td')[0].text)
                times[time] = bool(cell.xpath('table/tr/td/img'))

        return ret


    def stops(dom):
        return [
            strip(td.text)
            for td in dom.cssselect('div > table > tr > td')
        ]

    def trecho(dom):
        details = OrderedDict()
        for tr in dom.xpath('div/table/tr'):
            details[strip(tr.cssselect('td')[0].text)] = tr.cssselect('td input')[0].get('value')

        main_panels = dom.xpath('table/tr/td')

        ret = OrderedDict()
        ret["details"] = details
        ret["schedules"] = schedules(main_panels[0])
        ret["stops"] = stops(main_panels[1])
        ret["map"] = parseMap(pag_map);
        return ret

    trechos = [
        trecho(div)
        for div in pag_detalhes.cssselect('#tabs > div')
    ]

    ret = OrderedDict()
    ret["route_name"] = get_text(pag_detalhes, 'txtPesquisa')
    ret["company"] = get_text(pag_detalhes, 'txtEmpresa')
    ret["comments"] = get_text(pag_detalhes, 'txtObservacao')
    ret["updated"] = strip(pag_detalhes.cssselect('#conteudo font[size="1"]')[0].text.split('\n')[1])
    ret["route_url"] = url_detalhes
    ret["directions"] = trechos

    return ret

if __name__ == "__main__":
    import codecs
    import sys
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    routes = linhas()
    i=1
    for (linha, name) in routes.items():
        print('%d/%d    %s - %s' % (i, len(routes), linha, name))
        i+=1
        det = detalhes(linha)
        with file('out/%s.json' % linha, 'w') as f:
            f.write(json.dumps(det, indent=4))
        #print(json.dumps(det, indent=4))
