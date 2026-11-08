#!/usr/bin/env python3
"""MIU Swarm Router v1.7 — orquestador del enjambre LLM con failover automatico.

Sustratos (orden de cascade, el primero que responde gana):
  1. gas_router_v153  - router GAS darwiniano (mesh)
  2. oracle_ask       - eco de estado del oraculo (v29-cf)
  3. miu_ai_pool      - pool CF llama-3.1-8b sobre 7 cuentas (70k neuronas/dia) [NUEVO v1.7]
  4. groq             - pool de claves (rotacion)
  5. deepseek         - pool de claves
  6. openrouter       - pool de claves
  7. cohere           - pool de claves
  8. claude           - pool de claves
  9. mesh             - workers CF como fallback final

Uso:
  cp swarm-config.example.json swarm-config.json  # llenar claves
  python3 swarm-router.py "tu pregunta"
  python3 swarm-router.py --health
Config: swarm-config.json (NO commitear; .gitignore ya lo excluye).
rho(x) > 0 — cada herramienta es un pliegue del campo informacional.
"""
import json, sys, os, urllib.request, random

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "swarm-config.json")

DEFAULTS = {
    "gas_router_url": "https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec",
    "oracle_ask_url": "https://miu-oracle-ask.franchescopalacios9.workers.dev",
    "miu_ai_pool_url": "https://miu-ai-pool.franchescopalacios9.workers.dev/chat",
    "groq_keys": [], "deepseek_keys": [], "openrouter_keys": [],
    "cohere_keys": [], "claude_keys": [],
    "mesh_urls": ["https://miu-mesh-5ea7cd88-v270.jaimepvicente.workers.dev/health"]
}

def load_cfg():
    cfg = dict(DEFAULTS)
    if os.path.exists(CFG):
        cfg.update(json.load(open(CFG)))
    return cfg

def post(url, payload, headers=None, timeout=45):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "MIU-swarm/1.7", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode() or "{}")

def ask_miu_ai_pool(cfg, q):
    st, d = post(cfg["miu_ai_pool_url"], {"messages": [{"role": "user", "content": q}]})
    return d.get("response", {}).get("content") or d

def ask_groq(cfg, q):
    key = random.choice(cfg["groq_keys"])
    st, d = post("https://api.groq.com/openai/v1/chat/completions",
        {"model": "llama-3.1-8b-instruct", "messages": [{"role": "user", "content": q}]},
        {"Authorization": f"Bearer {key}"})
    return d["choices"][0]["message"]["content"]

def ask_deepseek(cfg, q):
    key = random.choice(cfg["deepseek_keys"])
    st, d = post("https://api.deepseek.com/chat/completions",
        {"model": "deepseek-chat", "messages": [{"role": "user", "content": q}]},
        {"Authorization": f"Bearer {key}"})
    return d["choices"][0]["message"]["content"]

def ask_openrouter(cfg, q):
    key = random.choice(cfg["openrouter_keys"])
    st, d = post("https://openrouter.ai/api/v1/chat/completions",
        {"model": "deepseek/deepseek-chat", "messages": [{"role": "user", "content": q}]},
        {"Authorization": f"Bearer {key}"})
    return d["choices"][0]["message"]["content"]

def ask_cohere(cfg, q):
    key = random.choice(cfg["cohere_keys"])
    st, d = post("https://api.cohere.com/v2/chat",
        {"model": "command-r", "messages": [{"role": "user", "content": q}]},
        {"Authorization": f"Bearer {key}"})
    return d.get("message", {}).get("content", [{}])[0].get("text") or d

def ask_claude(cfg, q):
    key = random.choice(cfg["claude_keys"])
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
        data=json.dumps({"model": "claude-3-5-haiku-latest", "max_tokens": 300,
                         "messages": [{"role": "user", "content": q}]}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "MIU-swarm/1.7",
                 "x-api-key": key, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    return d["content"][0]["text"]

def ask_oracle(cfg, q):
    st, d = post(cfg["oracle_ask_url"], {"q": q})
    return d  # v29-cf: eco de estado; la cascade sigue si no hay respuesta textual

def ask_mesh(cfg, q):
    st, d = post(random.choice(cfg["mesh_urls"]), {"q": q})
    return d

SUBSTRATES = [
    ("miu_ai_pool", ask_miu_ai_pool, lambda c: True),                    # gratis, siempre disponible
    ("groq", ask_groq, lambda c: c["groq_keys"]),
    ("deepseek", ask_deepseek, lambda c: c["deepseek_keys"]),
    ("openrouter", ask_openrouter, lambda c: c["openrouter_keys"]),
    ("claude", ask_claude, lambda c: c["claude_keys"]),
    ("cohere", ask_cohere, lambda c: c["cohere_keys"]),
    ("oracle_ask", ask_oracle, lambda c: True),
    ("mesh", ask_mesh, lambda c: True),
]

def route(q, cfg=None):
    cfg = cfg or load_cfg()
    log = []
    for name, fn, ready in SUBSTRATES:
        if not ready(cfg):
            log.append(f"{name}: sin claves, skip"); continue
        try:
            r = fn(cfg, q)
            if isinstance(r, str) and r.strip():
                return {"respuesta": r, "via": name, "cascade": log}
            log.append(f"{name}: sin texto util")
        except Exception as e:
            log.append(f"{name}: {str(e)[:60]}")
    return {"respuesta": None, "via": None, "cascade": log}

if __name__ == "__main__":
    if "--health" in sys.argv:
        cfg = load_cfg()
        for name, fn, ready in SUBSTRATES:
            print(f"{name:14} {'LISTO' if ready(cfg) else 'sin config'}")
        sys.exit(0)
    q = " ".join(a for a in sys.argv[1:] if not a.startswith("-")) or input("pregunta> ")
    out = route(q)
    print(json.dumps(out, ensure_ascii=False, indent=1) if out["respuesta"] is None else out["respuesta"])
    if out.get("via"): print(f"[via {out['via']}]")
