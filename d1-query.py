#!/usr/bin/env python3
"""MIU D1 Query — consulta el cerebro central D1."""
import urllib.request, json, sys, os

CF_TOKEN = os.environ.get('CF_TOKEN', '')
CF_ACCOUNT = os.environ.get('CF_ACCOUNT', '')
DB_ID = os.environ.get('D1_DB_ID', '')

def query(sql):
    url = f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/d1/database/{DB_ID}/query'
    data = json.dumps({'sql': sql}).encode()
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
        return result['result'][0]['results']

if __name__ == '__main__':
    if not CF_TOKEN or not CF_ACCOUNT or not DB_ID:
        print("Set CF_TOKEN, CF_ACCOUNT, D1_DB_ID environment variables")
        sys.exit(1)
    if len(sys.argv) < 2:
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
    else:
        sql = ' '.join(sys.argv[1:])
    rows = query(sql)
    print(json.dumps(rows, indent=2, ensure_ascii=False, default=str))
