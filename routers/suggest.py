"""Autocomplete (local dict) and care-tips / test-key (Gemini) API endpoints."""
import json
import logging
import re

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from services.plant_dict import search as dict_search
from services.ai_service import _make_client, _resolve_key
from config.settings import GEMINI_CHAT_MODEL

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


@router.get("/suggest")
def suggest(q: str = Query("", min_length=1)):
    """本地词库联想，无需 API，即时返回。"""
    return JSONResponse(dict_search(q.strip(), limit=6))


@router.get("/care-tips")
def care_tips(
    name: str = Query(...),
    species: str = Query(""),
    x_gemini_key: str = Header(default=""),
):
    plant_label = name + (f"（{species}）" if species else "")
    prompt = (
        f'请为"{plant_label}"提供养护知识，以 JSON 格式返回，包含以下字段：\n'
        '  water        — 浇水频率与方法（一句话）\n'
        '  light        — 光照需求（一句话）\n'
        '  temperature  — 适宜温度范围（一句话）\n'
        '  humidity     — 湿度要求（一句话）\n'
        '  fertilize    — 施肥建议（一句话）\n'
        '  common_issues — 常见问题及处理（两三句话）\n'
        "只返回 JSON 对象，不要任何解释。"
    )
    try:
        key = _resolve_key(x_gemini_key or None)
        client = _make_client(key)
        response = client.models.generate_content(model=GEMINI_CHAT_MODEL, contents=prompt)
        data = json.loads(_clean_json(response.text))
        return JSONResponse(data)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        log.warning("care-tips failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=502)


@router.post("/test-key")
def test_key(x_gemini_key: str = Header(default="")):
    """验证用户提供的 Gemini Key 是否有效。"""
    try:
        key = _resolve_key(x_gemini_key or None)
        client = _make_client(key)
        client.models.generate_content(
            model=GEMINI_CHAT_MODEL,
            contents="回复数字1",
        )
        return JSONResponse({"ok": True})
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "401" in msg:
            return JSONResponse({"ok": False, "error": "Key 无效，请检查是否复制正确"})
        if "429" in msg:
            return JSONResponse({"ok": False, "error": "Key 有效但配额已用完"})
        return JSONResponse({"ok": False, "error": msg})
