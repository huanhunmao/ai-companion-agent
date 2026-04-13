import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
try:
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
except ImportError:
    ProxyHeadersMiddleware = None

from auth_deps import require_app_key
from llm_clients import create_client_by_model
from memory_store import (
    get_session_memories,
    add_session_memories,
    delete_session_memories,
    set_session_memories,
)

load_dotenv()

app = FastAPI()
WEB_DIST_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"

# 信任反向代理（Nginx / 云平台）转发的真实客户端 IP，便于限流
if ProxyHeadersMiddleware is not None:
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

_cors_raw = (os.getenv("CORS_ORIGINS") or "").strip()
if _cors_raw:
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
else:
    _cors_origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "moonshot/kimi-k2-0905-preview")


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    session_id: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1
    max_tokens: Optional[int] = 1200
    memory_enabled: Optional[bool] = True


class ChatResponse(BaseModel):
    reply: str
    meta: Optional[dict] = None


class MemoryResponse(BaseModel):
    memories: List[str]


class UpdateMemoryRequest(BaseModel):
    memories: List[str]


def build_memory_prompt(memories: List[str]) -> str:
    if not memories:
        return ""

    lines = "\n".join([f"- {item}" for item in memories])
    return f"""以下是你已经记住的用户信息，请在回复时自然参考，但不要生硬复述：
{lines}
"""


def extract_user_memories(user_text: str, model_name: Optional[str] = None) -> List[str]:
    text = (user_text or "").strip()
    if not text:
        return []

    prompt = f"""
你是一个信息抽取助手。
请从下面这段用户发言中，提取“适合长期记忆的用户事实”。

要求：
1. 只提取长期有价值的信息，比如：职业、兴趣、目标、偏好、正在做的项目
2. 不要提取一次性寒暄
3. 每条一句话，简洁
4. 最多返回 5 条
5. 只返回 JSON 数组，不要输出其他内容

用户发言：
{text}
"""

    try:
        client, config = create_client_by_model(model_name or DEFAULT_MODEL_NAME)

        completion = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": "你是一个严谨的用户事实提取助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "[]"
        print("memory extract raw content:", content)

        result = json.loads(content)

        if isinstance(result, list):
            parsed = [str(item).strip() for item in result if str(item).strip()]
            if parsed:
                print("memory extract parsed:", parsed)
                return parsed

        fallback_keywords = ["我是", "我在", "我最近", "我想", "我希望", "我主要", "我平时", "我的目标"]
        if any(keyword in text for keyword in fallback_keywords):
            print("memory extract fallback:", [text])
            return [text]

        print("memory extract parsed: []")
        return []
    except Exception as e:
        print("extract_user_memories error:", e)
        return []


def build_final_messages(messages: List[dict], session_id: str = "", memory_enabled: bool = True):
    session_memories = get_session_memories(session_id or "") if memory_enabled else []
    memory_prompt = build_memory_prompt(session_memories) if memory_enabled else ""

    final_messages = []
    for item in messages:
        if item["role"] == "system":
            final_messages.append({
                "role": "system",
                "content": f'{item["content"]}\n\n{memory_prompt}'.strip()
            })
        else:
            final_messages.append(item)

    return final_messages, session_memories


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
def chat(
    request: Request,
    req: ChatRequest,
    _: None = Depends(require_app_key),
):
    messages = [m.model_dump() for m in req.messages]
    final_messages, session_memories = build_final_messages(
        messages,
        req.session_id or "",
        req.memory_enabled if req.memory_enabled is not None else True,
    )

    print("session_memories:", session_memories)

    start_time = time.perf_counter()
    meta = None

    try:
        client, config = create_client_by_model(req.model or DEFAULT_MODEL_NAME)

        completion = client.chat.completions.create(
            model=config["model"],
            messages=final_messages,
            temperature=req.temperature or 0.7,
            top_p=req.top_p or 1,
            max_tokens=req.max_tokens or 1200,
        )
        reply = completion.choices[0].message.content or ""

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        usage = getattr(completion, "usage", None)

        meta = {
            "provider": config["provider"],
            "model": req.model or DEFAULT_MODEL_NAME,
            "duration_ms": duration_ms,
            "reply_at": datetime.now().isoformat(),
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            },
        }
    except Exception as e:
        print("chat error:", e)
        reply = "AI服务异常，请稍后再试"

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        meta = {
            "provider": None,
            "model": req.model or DEFAULT_MODEL_NAME,
            "duration_ms": duration_ms,
            "reply_at": datetime.now().isoformat(),
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }

    if req.session_id:
        latest_user_text = ""
        for item in reversed(messages):
            if item["role"] == "user":
                latest_user_text = item["content"]
                break

        print("session_id:", req.session_id)
        print("latest_user_text:", latest_user_text)

        if latest_user_text:
            new_memories = extract_user_memories(latest_user_text, req.model or DEFAULT_MODEL_NAME)
            print("new_memories:", new_memories)
            add_session_memories(req.session_id, new_memories)

    return ChatResponse(reply=reply, meta=meta)


@app.post("/api/chat/stream")
@limiter.limit("60/minute")
def chat_stream(
    request: Request,
    req: ChatRequest,
    _: None = Depends(require_app_key),
):
    messages = [m.model_dump() for m in req.messages]
    final_messages, session_memories = build_final_messages(
        messages,
        req.session_id or "",
        req.memory_enabled if req.memory_enabled is not None else True,
    )

    print("stream session_memories:", session_memories)

    def generate():
        full_reply = ""
        start_time = time.perf_counter()
        provider = None
        model_name = req.model or DEFAULT_MODEL_NAME

        try:
            client, config = create_client_by_model(model_name)
            provider = config["provider"]

            stream = client.chat.completions.create(
                model=config["model"],
                messages=final_messages,
                temperature=req.temperature or 0.7,
                top_p=req.top_p or 1,
                max_tokens=req.max_tokens or 1200,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_reply += delta
                    yield f"data: {json.dumps({'type': 'chunk', 'content': delta}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print("stream chat error:", e)
            yield f"data: {json.dumps({'type': 'error', 'content': 'AI服务异常，请稍后再试'}, ensure_ascii=False)}\n\n"
            return

        if req.session_id:
            latest_user_text = ""
            for item in reversed(messages):
                if item["role"] == "user":
                    latest_user_text = item["content"]
                    break

            print("stream session_id:", req.session_id)
            print("stream latest_user_text:", latest_user_text)

            if latest_user_text:
                new_memories = extract_user_memories(latest_user_text, model_name)
                print("stream new_memories:", new_memories)
                add_session_memories(req.session_id, new_memories)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        meta = {
            "provider": provider,
            "model": model_name,
            "duration_ms": duration_ms,
            "reply_at": datetime.now().isoformat(),
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }

        yield f"data: {json.dumps({'type': 'done', 'content': full_reply, 'meta': meta}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/memory/{session_id}", response_model=MemoryResponse)
@limiter.limit("120/minute")
def get_memory(
    request: Request,
    session_id: str,
    _: None = Depends(require_app_key),
):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")
    return MemoryResponse(memories=get_session_memories(session_id))


@app.put("/api/memory/{session_id}", response_model=MemoryResponse)
@limiter.limit("120/minute")
def update_memory(
    request: Request,
    session_id: str,
    req: UpdateMemoryRequest,
    _: None = Depends(require_app_key),
):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")

    set_session_memories(session_id, req.memories)
    return MemoryResponse(memories=get_session_memories(session_id))


@app.delete("/api/session/{session_id}")
@limiter.limit("120/minute")
def delete_session(
    request: Request,
    session_id: str,
    _: None = Depends(require_app_key),
):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")

    delete_session_memories(session_id)
    return {"ok": True}


if WEB_DIST_DIR.exists():
    assets_dir = WEB_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="web-assets")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(WEB_DIST_DIR / "index.html")


    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        candidate = WEB_DIST_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST_DIR / "index.html")
