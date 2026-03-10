#!/usr/bin/env python3
"""BlackRoad AI Chain — Multi-node distributed inference"""
import time, json, asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="BlackRoad AI Chain")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

NODES = {
    "octavia": {"ip": "127.0.0.1", "port": 11437, "model": "deepseek-r1:1.5b",   "role": "reasoning"},
    "aria":    {"ip": "127.0.0.1", "port": 11438, "model": "qwen2.5-coder:3b",   "role": "code"},
    "lucidia": {"ip": "127.0.0.1", "port": 11436, "model": "tinyllama:latest",    "role": "personality"},
    "alice":   {"ip": "127.0.0.1", "port": 11435, "model": "tinyllama:latest",    "role": "fallback"},
}

async def ollama_generate(ip, port, model, prompt, timeout=300):
    url = f"http://{ip}:{port}/api/generate"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json={"model": model, "prompt": prompt, "stream": False})
        return r.json()["response"]

async def node_health(name, node):
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"http://{node['ip']}:{node['port']}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            return {"name": name, "status": "online", "role": node["role"], "models": models}
    except:
        return {"name": name, "status": "offline", "role": node["role"], "models": []}

@app.get("/health")
async def health():
    results = await asyncio.gather(*[node_health(n, v) for n, v in NODES.items()])
    return {"nodes": results, "online": sum(1 for r in results if r["status"] == "online")}

@app.post("/chain")
async def chain(body: dict):
    prompt = body.get("prompt", "")
    if not prompt:
        return {"error": "prompt required"}

    t0 = time.time()
    nodes_used = []

    # Step 1: Reasoning (Octavia → fallback Alice)
    reasoning = None
    for name in ["octavia", "alice"]:
        node = NODES[name]
        try:
            reasoning = await ollama_generate(node["ip"], node["port"], node["model"],
                f"Think step by step about this question. Be concise.\n\n{prompt}")
            nodes_used.append({"node": name, "model": node["model"], "role": "reasoning"})
            break
        except:
            continue

    if not reasoning:
        return {"error": "all reasoning nodes down", "latency_ms": int((time.time()-t0)*1000)}

    # Step 2: Personality (Lucidia → fallback Alice)
    response = None
    for name in ["lucidia", "alice"]:
        node = NODES[name]
        try:
            response = await ollama_generate(node["ip"], node["port"], node["model"],
                f"You are a thoughtful AI. Take this analysis and give a clear, helpful answer.\n\nAnalysis: {reasoning}\n\nOriginal question: {prompt}\n\nAnswer:")
            nodes_used.append({"node": name, "model": node["model"], "role": "personality"})
            break
        except:
            continue

    if not response:
        response = reasoning  # fallback to raw reasoning

    return {
        "prompt": prompt,
        "reasoning": reasoning,
        "response": response,
        "nodes_used": nodes_used,
        "latency_ms": int((time.time()-t0)*1000)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
