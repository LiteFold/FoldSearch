# app.py – minimal but working multi‑agent FastAPI server
# -------------------------------------------------------
"""Run with
    pip install fastapi uvicorn sse-starlette openai python-dotenv
    uvicorn app:app --reload
and POST a task:
    curl -X POST http://localhost:8000/task \
         -H 'Content-Type: application/json' \
         -d '{"user_goal":"Summarise recent papers on SSE and add 2+2"}'
then open /stream/<job_id> to watch live updates.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any, Callable, Dict

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from openai import AsyncOpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# ---------------------------------------------------------------------------
# Environment & client
# ---------------------------------------------------------------------------
load_dotenv()
openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# FastAPI setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Cursor‑style multi‑agent orchestrator")
JOBS: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class Task(BaseModel):
    """Incoming request body"""

    user_goal: str

# ---------------------------------------------------------------------------
# Helper to build correct OpenAI tool schema
# ---------------------------------------------------------------------------

def make_tool(
    *,
    name: str,
    description: str,
    props: Dict[str, Any],
    required: list[str],
) -> Dict[str, Any]:
    """Return a fully‑formed tool schema ("type":"function" wrapper included)."""

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        },
    }

# ---------------------------------------------------------------------------
# Very tiny toolbox – plug in real stuff later
# ---------------------------------------------------------------------------
async def web_search(q: str) -> str:
    # TODO: replace with a real web search + scrape
    return f"Top result for '{q}'"


async def calculate(expr: str) -> str:
    return str(eval(expr))  # noqa: S307 – demo‑only


TOOLS: Dict[str, Callable[[str], asyncio.Future]] = {
    "web_search": web_search,
    "calculate": calculate,
}

# ---------------------------------------------------------------------------
# Agent execution loop
# ---------------------------------------------------------------------------
async def run_agent(name: str, subtask: str, job_id: str) -> str:
    """One agent plans its own tool calls until it produces an answer."""

    # Build agent‑specific tool list
    agent_schema = [
        make_tool(
            name=tool_name,
            description=f"Invoke internal tool {tool_name}",
            props={"arg": {"type": "string"}},
            required=["arg"],
        )
        for tool_name in TOOLS
    ]

    sys_prompt = f"You are the {name} agent. Think step‑by‑step, decide which tools to call, and produce a final answer when done."
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": subtask},
    ]

    while True:
        resp = await openai.chat.completions.create(
            model="gpt-4o-mini",
            tools=agent_schema,
            messages=messages,
            # default tool_choice="auto"
            stream=False,
        )

        msg = resp.choices[0].message

        # 1️⃣ The model wants the host to call a tool ---------------------------------
        if msg.tool_calls:
            # First, add the assistant message with tool calls to the conversation
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": call.type,
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    }
                    for call in msg.tool_calls
                ]
            })
            
            # Then process each tool call and add tool responses
            for call in msg.tool_calls:
                fn_name = call.function.name
                fn_args = json.loads(call.function.arguments)
                result = await TOOLS[fn_name](fn_args["arg"])

                # log progress for SSE consumers
                JOBS[job_id]["log"].append(f"{name}:{fn_name} → {result}")

                # add a tool‑role message so the model can continue
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )
        # 2️⃣ The model produced a final answer --------------------------------------
        else:
            JOBS[job_id]["log"].append(f"{name}: ✅ {msg.content}")
            return msg.content  # may be ignored by caller


# ---------------------------------------------------------------------------
# Orchestrator – picks which agent handles which sub‑task
# ---------------------------------------------------------------------------
async def orchestrate(goal: str, job_id: str) -> None:
    agents = ["Research", "Math"]

    fn_schema = [
        make_tool(
            name="run_agent",
            description="Choose which specialised agent executes a sub‑goal",
            props={
                "agent": {"type": "string", "enum": agents},
                "input": {"type": "string"},
            },
            required=["agent", "input"],
        )
    ]

    messages = [
        {"role": "system", "content": "Break the user goal into ordered agent calls."},
        {"role": "user", "content": goal},
    ]

    resp = await openai.chat.completions.create(
        model="gpt-4o-mini",
        tools=fn_schema,
        messages=messages,
        stream=False,
    )

    plan_calls = resp.choices[0].message.tool_calls or []
    for call in plan_calls:
        args = json.loads(call.function.arguments)
        await run_agent(args["agent"], args["input"], job_id)

    JOBS[job_id]["done"] = True


# ---------------------------------------------------------------------------
# FastAPI routes
# ---------------------------------------------------------------------------
@app.post("/task")
async def submit(task: Task, bg: BackgroundTasks):
    """Accept a high‑level user goal and start background orchestration."""

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"log": [], "done": False}
    bg.add_task(orchestrate, task.user_goal, job_id)
    return {"job_id": job_id}


@app.get("/stream/{job_id}")
async def stream(job_id: str):
    """Server‑Sent Events endpoint that streams job progress."""

    async def event_generator():
        prev_len = 0
        while not JOBS[job_id]["done"]:
            await asyncio.sleep(1)
            while prev_len < len(JOBS[job_id]["log"]):
                yield {
                    "event": "update",
                    "data": JOBS[job_id]["log"][prev_len],
                }
                prev_len += 1
        yield {"event": "done", "data": "COMPLETE"}

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Dev‑time entry‑point ("python app.py")
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
