#!/usr/bin/env python3
"""MIU GAS Router V153 — router darwiniano de Apps Script."""
import urllib.request, json, sys

ROUTER_URL = 'https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec'

def phi():
    req = urllib.request.Request(ROUTER_URL)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

if __name__ == '__main__':
    data = phi()
    print(json.dumps(data, indent=2, ensure_ascii=False))
