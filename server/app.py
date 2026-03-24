import os
import json
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from typing import List, Literal, Optional
from fastapi import FastAPI, HTTPException
from memory_store import get_session_memories, add_session_memories, delete_session_memories

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1"),
)

MODEL_NAME = os.getenv("MOONSHOT_MODEL", "kimi-k2-0905-preview")


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str

class MemoryResponse(BaseModel):
    memories: List[str]

def build_memory_prompt(memories: List[str]) -> str:
    if not memories:
        return ""

    lines = "\n".join([f"- {item}" for item in memories])
    return f"""以下是你已经记住的用户信息，请在回复时自然参考，但不要生硬复述：
{lines}
"""


def extract_user_memories(user_text: str) -> List[str]:
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
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个严谨的用户事实提取助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "[]"
        print("memory extract raw content:", content)

        import json
        result = json.loads(content)

        if isinstance(result, list):
            parsed = [str(item).strip() for item in result if
                      str(item).strip()]
            print("memory extract parsed:", parsed)
            return parsed

        print("memory extract parsed: []")
        return []
    except Exception as e:
        print("extract_user_memories error:", e)
        return []

def build_final_messages(messages: List[dict], session_id: str = ""):
    session_memories = get_session_memories(session_id or "")
    memory_prompt = build_memory_prompt(session_memories)

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
def chat(req: ChatRequest):
    messages = [m.model_dump() for m in req.messages]
    final_messages, session_memories = build_final_messages(messages, req.session_id or "")

    print("session_memories:", session_memories)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=final_messages,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content or ""
    except Exception as e:
        print("chat error:", e)
        reply = "AI服务异常，请稍后再试"

    if req.session_id:
        latest_user_text = ""
        for item in reversed(messages):
            if item["role"] == "user":
                latest_user_text = item["content"]
                break

        print("session_id:", req.session_id)
        print("latest_user_text:", latest_user_text)

        if latest_user_text:
            new_memories = extract_user_memories(latest_user_text)
            print("new_memories:", new_memories)
            add_session_memories(req.session_id, new_memories)

    return ChatResponse(reply=reply)

@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    messages = [m.model_dump() for m in req.messages]
    final_messages, session_memories = build_final_messages(messages, req.session_id or "")

    print("stream session_memories:", session_memories)

    def generate():
        full_reply = ""

        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=final_messages,
                temperature=0.7,
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
                new_memories = extract_user_memories(latest_user_text)
                print("stream new_memories:", new_memories)
                add_session_memories(req.session_id, new_memories)

        yield f"data: {json.dumps({'type': 'done', 'content': full_reply}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/api/memory/{session_id}", response_model=MemoryResponse)
def get_memory(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")
    return MemoryResponse(memories=get_session_memories(session_id))

@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")

    delete_session_memories(session_id)
    return {"ok": True}