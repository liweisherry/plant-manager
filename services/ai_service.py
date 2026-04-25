"""Gemini AI integration — plant identification and care advice."""
import logging
from typing import Optional

from google import genai
from PIL import Image
import io
from sqlalchemy.orm import Session

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_CHAT_MODEL,
    GEMINI_VISION_MODEL,
    UPLOAD_DIR,
)
from db.models import AIResult

log = logging.getLogger(__name__)


def _make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def _resolve_key(user_key: Optional[str]) -> str:
    """用请求里的 Key，没有则降级到服务器 env。"""
    key = (user_key or "").strip() or GEMINI_API_KEY
    if not key:
        raise ValueError("未设置 Gemini API Key，请前往「设置」页面填写。")
    return key


def _load_image(filename: str) -> Image.Image:
    path = UPLOAD_DIR / "plants" / filename
    return Image.open(io.BytesIO(path.read_bytes()))


# ── Identify ──────────────────────────────────────────────────────────────────

def identify_plant(
    db: Session,
    plant_id: int,
    photo_id: int,
    filename: str,
    api_key: Optional[str] = None,
) -> AIResult:
    client = _make_client(_resolve_key(api_key))
    prompt = (
        "请根据图片识别这株植物。\n"
        "用中文回答，包含：\n"
        "1. 植物名称（中文 + 拉丁学名）\n"
        "2. 主要特征\n"
        "3. 基本养护要点（浇水频率、光照、温度）\n"
        "4. 常见问题\n"
        "格式清晰，分段落。"
    )
    img = _load_image(filename)
    response = client.models.generate_content(
        model=GEMINI_VISION_MODEL,
        contents=[prompt, img],
    )
    text = response.text
    species = _extract_species(text)

    usage = response.usage_metadata
    result = AIResult(
        plant_id=plant_id,
        photo_id=photo_id,
        request_type="identify",
        prompt=prompt,
        response_text=text,
        identified_species=species,
        model=GEMINI_VISION_MODEL,
        input_tokens=usage.prompt_token_count if usage else None,
        output_tokens=usage.candidates_token_count if usage else None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def _extract_species(text: str) -> str:
    for line in text.splitlines():
        line = line.strip().lstrip("1.# ").strip()
        if line:
            return line[:200]
    return ""


# ── Care Advice ───────────────────────────────────────────────────────────────

def get_care_advice(
    db: Session,
    plant_id: int,
    plant_name: str,
    species: Optional[str],
    question: str,
    photo_filename: Optional[str] = None,
    photo_id: Optional[int] = None,
    api_key: Optional[str] = None,
) -> AIResult:
    client = _make_client(_resolve_key(api_key))
    system = (
        "你是一位经验丰富的植物养护专家，擅长中文解答。"
        "回答时简洁实用，直接给出可操作的建议。"
    )
    plant_ctx = f"植物：{plant_name}"
    if species:
        plant_ctx += f"（{species}）"
    user_text = f"{plant_ctx}\n\n问题：{question}"

    contents: list = [system + "\n\n" + user_text]
    if photo_filename:
        try:
            contents.append(_load_image(photo_filename))
        except Exception as e:
            log.warning("Could not load photo %s: %s", photo_filename, e)

    model_name = GEMINI_VISION_MODEL if photo_filename else GEMINI_CHAT_MODEL
    response = client.models.generate_content(model=model_name, contents=contents)
    text = response.text

    usage = response.usage_metadata
    result = AIResult(
        plant_id=plant_id,
        photo_id=photo_id,
        request_type="advice",
        prompt=user_text,
        response_text=text,
        model=model_name,
        input_tokens=usage.prompt_token_count if usage else None,
        output_tokens=usage.candidates_token_count if usage else None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
