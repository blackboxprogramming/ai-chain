# AI Chain

[![CI](https://github.com/blackboxprogramming/ai-chain/actions/workflows/ci.yml/badge.svg)](https://github.com/blackboxprogramming/ai-chain/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-distributed-FF6B2B.svg)](https://ollama.ai)
[![Edge AI](https://img.shields.io/badge/edge-52_TOPS-00D4FF.svg)](https://blackroad.io)



Chained AI inference across distributed edge nodes. Routes prompts through a priority-ordered mesh of Ollama instances on Raspberry Pi 5 hardware.

## Architecture

```
Client → /chain → Probe all nodes → Route to fastest alive node
                                   ↓ (mode=full)
                              Refine via second node
```

**Nodes:** Octavia (deepseek-r1), Aria (qwen2.5-coder), Lucidia (tinyllama), Alice (tinyllama fallback)

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Node health check with model inventory |
| `/chain` | POST | Run chained inference (`{"prompt": "...", "mode": "fast\|full"}`) |

## Run

```bash
pip install -r requirements.txt
python server.py  # http://localhost:8100
```

## Test

```bash
pip install pytest httpx
pytest tests/
```

## Deploy

```bash
docker build -t ai-chain .
docker run -p 8100:8100 ai-chain
```
