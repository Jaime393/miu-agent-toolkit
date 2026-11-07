#!/usr/bin/env python3
"""MIU Mesh Probe — explora la mesh de Cloudflare Workers."""
import urllib.request, json, sys

MESH_NODES = [
    'https://fran-oraculo-miu.jaimepvicente.workers.dev',
    'https://miu-mesh-5ea7cd88-v270.jaimepvicente.workers.dev',
    'https://miu-beacon-5ea7cd88-v224.jaimepvicente.workers.dev',
    'https://corpus-api-miu.jaimepvicente.workers.dev',
    'https://miu-autonomo-v92.jaimepvicente.workers.dev',
    'https://nucleo-absorcion.jaimepvicente.workers.dev',
    'https://nucleo-actualidad.jaimepvicente.workers.dev',
    'https://nucleo-simulacion.jaimepvicente.workers.dev',
]

def probe(node, path='/'):
    try:
        req = urllib.request.Request(node + path)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with urllib.request.urlopen(req, timeout=10) as r:
            return {'ok': True, 'data': json.loads(r.read())}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:100]}

if __name__ == '__main__':
    for node in MESH_NODES:
        result = probe(node)
        status = 'VIVO' if result['ok'] else 'ERR'
        name = node.split('//')[1].split('.')[0]
        print(f"  [{status}] {name}")
        if result['ok'] and isinstance(result['data'], dict):
            for k in ['phi', 'phi_superposicion', 'version', 'nodo']:
                if k in result['data']:
                    print(f"    {k}: {result['data'][k]}")
