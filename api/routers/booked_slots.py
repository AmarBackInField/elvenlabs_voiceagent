"""
Booked Slots & Datetime Tools Router.
Proxy for Montessori booked-slots and ElevenLabs webhook tools (booked slots, current datetime CST).
"""

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from api.schemas import ErrorResponse


# Webhook base URL for ElevenLabs to call (e.g. https://elvenlabs-voiceagent.onrender.com)
WEBHOOK_BASE_URL = (os.getenv("WEBHOOK_BASE_URL", "https://elvenlabs-voiceagent.onrender.com") or "").rstrip("/")
BOOKED_SLOTS_API_URL = os.getenv(
    "BOOKED_SLOTS_API_URL",
    "https://montessori-enrollment-ai-backend.onrender.com/api/voice/booked-slots",
)
DEFAULT_SCHOOL_ID = os.getenv("SCHOOL_ID", "69a2a7bf84844ca0d53116d6")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = (os.getenv("ELEVENLABS_BASE_URL", "https://api.eu.residency.elevenlabs.io") or "").rstrip("/")

router = APIRouter(
    prefix="",
    tags=["Booked Slots"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


class RegisterToolRequest(BaseModel):
    """Register booked-slots webhook tool with ElevenLabs."""
    school_id: str
    agent_id: str | None = None  # if provided, tool is attached to this agent after creation


class RegisterDatetimeToolRequest(BaseModel):
    """Register current datetime (CST) webhook tool and attach to agent."""
    agent_id: str


async def _attach_tool_to_agent(client: httpx.AsyncClient, agent_id: str, tool_id: str) -> tuple[bool, str | None]:
    """GET agent, add tool_id to workflow.prompt.tool_ids, PATCH agent. Returns (success, error_message)."""
    get_resp = await client.get(
        f"{ELEVENLABS_BASE_URL}/v1/convai/agents/{agent_id}",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
    )
    if get_resp.status_code != 200:
        return False, f"Could not load agent: {get_resp.status_code}"
    agent = get_resp.json()
    existing_ids = []
    for path in (("workflow", "prompt"), ("conversation_config", "agent", "prompt")):
        node = agent
        for key in path:
            node = (node or {}).get(key)
            if node is None:
                break
        if node and isinstance(node.get("tool_ids"), list):
            existing_ids = list(node["tool_ids"])
            break
    if tool_id not in existing_ids:
        existing_ids.append(tool_id)
    workflow = (agent.get("workflow") or {}).copy()
    prompt = (workflow.get("prompt") or {}).copy()
    prompt["tool_ids"] = existing_ids
    workflow["prompt"] = prompt
    patch_resp = await client.patch(
        f"{ELEVENLABS_BASE_URL}/v1/convai/agents/{agent_id}",
        json={"workflow": workflow},
        headers={"Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY},
    )
    if patch_resp.status_code not in (200, 204):
        return False, f"PATCH agent failed: {patch_resp.status_code} - {patch_resp.text}"
    return True, None


def _validate_date_format(value: str) -> str:
    """Expect YYYY-MM-DD."""
    try:
        date.fromisoformat(value)
        return value
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD (e.g. 2025-03-20)")


@router.get(
    "/booked-slots",
    summary="Get Booked Slots",
    description="Get available and booked slots for the school on the given date. Used by ElevenLabs get_booked_slots webhook.",
)
async def get_booked_slots(
    date_param: str = Query(..., alias="date", description="Date in YYYY-MM-DD format (e.g. 2025-03-20)"),
    school_id: str | None = Query(None, alias="schoolId", description="School ID (optional, defaults to env SCHOOL_ID)"),
):
    """Get available and booked slots for the school on the given date."""
    date_param = _validate_date_format(date_param)
    sid = (school_id or DEFAULT_SCHOOL_ID).strip()
    if not sid:
        raise HTTPException(status_code=422, detail="schoolId is required or set SCHOOL_ID in .env")
    url = f"{BOOKED_SLOTS_API_URL.rstrip('/')}?schoolId={sid}&date={date_param}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


@router.post(
    "/register-tool",
    summary="Register Tool",
    description="Register the booked-slots webhook tool with ElevenLabs for the given school_id. Optionally attach to an agent.",
)
async def register_tool(body: RegisterToolRequest):
    """Register an ElevenLabs webhook tool for the given school_id. The tool only asks the agent for 'date' (YYYY-MM-DD); schoolId is fixed."""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured in .env")
    if not ELEVENLABS_BASE_URL:
        raise HTTPException(status_code=503, detail="ELEVENLABS_BASE_URL not configured in .env")
    school_id = body.school_id.strip()
    if not school_id:
        raise HTTPException(status_code=422, detail="school_id cannot be empty")

    base = (WEBHOOK_BASE_URL or "http://localhost:8000").rstrip("/")
    webhook_url = f"{base}/api/v1/booked-slots"
    payload = {
        "tool_config": {
            "type": "webhook",
            "name": "get_booked_slots",
            "description": "Get available and booked time slots for the school on a given date. Use when the user asks about availability, open slots, or booking for a specific date. Returns business hours, available slots (15-minute intervals), and already booked slots.",
            "api_schema": {
                "url": webhook_url,
                "method": "GET",
                "query_params_schema": {
                    "properties": {
                        "schoolId": {"type": "string", "constant_value": school_id},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format (e.g. 2025-03-20)"},
                    },
                    "required": ["schoolId", "date"],
                },
            },
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{ELEVENLABS_BASE_URL}/v1/convai/tools",
            json=payload,
            headers={"Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"ElevenLabs API error: {resp.status_code} - {resp.text}")
        tool_data = resp.json()
        tool_id = tool_data.get("tool_id") or tool_data.get("id")
        if body.agent_id and tool_id:
            agent_id = body.agent_id.strip()
            ok, err = await _attach_tool_to_agent(client, agent_id, tool_id)
            if not ok:
                return {"tool_created": tool_data, "tool_id": tool_id, "attach_error": err}
            return {"tool_created": tool_data, "tool_id": tool_id, "attached_to_agent": agent_id}
    return tool_data


# Current date/time in CST (for ElevenLabs datetime tool)
CST = ZoneInfo("America/Chicago")


@router.get(
    "/current-datetime-cst",
    summary="Get Current Datetime CST",
    description="Returns current date and time in CST (America/Chicago). Used as webhook by ElevenLabs get_current_datetime_cst tool.",
)
async def get_current_datetime_cst():
    """Returns current date and time in CST (America/Chicago)."""
    now = datetime.now(CST)
    return {
        "timezone": "CST",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime_iso": now.isoformat(),
        "day_of_week": now.strftime("%A"),
    }


@router.post(
    "/register-datetime-tool",
    summary="Register Datetime Tool",
    description="Register the current date/time (CST) webhook tool with ElevenLabs and attach it to the given agent.",
)
async def register_datetime_tool(body: RegisterDatetimeToolRequest):
    """Register the current date/time (CST) webhook tool with ElevenLabs and attach it to the given agent. Webhook URL uses WEBHOOK_BASE_URL (default https://elvenlabs-voiceagent.onrender.com)."""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured in .env")
    if not ELEVENLABS_BASE_URL:
        raise HTTPException(status_code=503, detail="ELEVENLABS_BASE_URL not configured in .env")
    agent_id = (body.agent_id or "").strip()
    if not agent_id:
        raise HTTPException(status_code=422, detail="agent_id cannot be empty")

    base = WEBHOOK_BASE_URL or "http://localhost:8000"
    webhook_url = f"{base.rstrip('/')}/api/v1/current-datetime-cst"

    payload = {
        "tool_config": {
            "type": "webhook",
            "name": "get_current_datetime_cst",
            "description": "Get the current date and time in CST (Central Standard Time) timezone. Use when the user asks what day it is, what time it is, or today's date.",
            "api_schema": {
                "url": webhook_url,
                "method": "GET",
            },
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        create_resp = await client.post(
            f"{ELEVENLABS_BASE_URL}/v1/convai/tools",
            json=payload,
            headers={"Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY},
        )
        if create_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"ElevenLabs create tool error: {create_resp.status_code} - {create_resp.text}",
            )
        tool_data = create_resp.json()
        tool_id = tool_data.get("tool_id") or tool_data.get("id")
        if not tool_id:
            return {"tool_created": tool_data, "message": "Tool created; add it via Agent Tools → Add tool in the ElevenLabs UI."}

        ok, err = await _attach_tool_to_agent(client, agent_id, tool_id)
        if not ok:
            return {
                "tool_created": tool_data,
                "tool_id": tool_id,
                "attach_error": err or "Attach failed. Add manually: Agent Tools → Add tool → get_current_datetime_cst.",
            }
    return {"tool_created": tool_data, "attached_to_agent": agent_id, "tool_id": tool_id}
