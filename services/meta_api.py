import os
import httpx
from pathlib import Path

BASE = "https://graph.facebook.com/v22.0"
_ENV_PATH = Path(__file__).parent.parent / ".env"

def _token() -> str:
    # Đọc trực tiếp từ file .env mỗi lần gọi
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("FB_ACCESS_TOKEN="):
                t = line.split("=", 1)[1].strip()
                if t:
                    return t
    t = os.getenv("FB_ACCESS_TOKEN", "")
    if not t:
        raise ValueError("FB_ACCESS_TOKEN chưa được cấu hình trong .env")
    return t

async def _post(path: str, data: dict) -> dict:
    data["access_token"] = _token()
    import json as _j
    debug = {k: v for k, v in data.items() if k != "access_token"}
    with open(Path(__file__).parent.parent / "meta_debug.log", "a", encoding="utf-8") as f:
        f.write(f"\n[POST] {path}\n{_j.dumps(debug, indent=2, ensure_ascii=False)}\n")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE}{path}", data=data)
    result = r.json()
    if "error" in result:
        e = result["error"]
        detail = e.get('error_user_msg') or e.get('error_user_title') or e.get('message', '')
        subcode = e.get('error_subcode', '')
        sent = {k: v for k, v in debug.items() if k in ('bid_strategy','optimization_goal','billing_event','daily_budget')}
        raise RuntimeError(f"Meta API error {e.get('code')}{f'/{subcode}' if subcode else ''}: {detail} | sent={sent}")
    return result

async def upload_image(acc_id: str, file_bytes: bytes, filename: str) -> str:
    """Upload ảnh lên Meta, trả về image_hash."""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{BASE}/{acc_id}/adimages",
            data={"access_token": _token()},
            files={"filename": (filename, file_bytes)},
        )
    result = r.json()
    if "error" in result:
        e = result["error"]
        raise RuntimeError(f"Upload image error {e.get('code')}: {e.get('message')}")
    images = result.get("images", {})
    entry = next(iter(images.values()), None)
    if not entry:
        raise RuntimeError("Upload image: không nhận được hash từ Meta")
    return entry["hash"]

async def upload_video(acc_id: str, file_bytes: bytes, filename: str) -> str:
    """Upload video lên Meta, trả về video_id."""
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            f"{BASE}/{acc_id}/advideos",
            data={"access_token": _token(), "name": filename},
            files={"source": (filename, file_bytes)},
        )
    result = r.json()
    if "error" in result:
        e = result["error"]
        raise RuntimeError(f"Upload video error {e.get('code')}: {e.get('message')}")
    vid_id = result.get("id")
    if not vid_id:
        raise RuntimeError("Upload video: không nhận được video_id từ Meta")
    return str(vid_id)

async def create_campaign(acc_id: str, name: str, objective: str, daily_budget_cents: int | None,
                          special_ad_categories: list, bid_strategy: str = "LOWEST_COST_WITHOUT_CAP") -> str:
    import json as _json
    payload = {
        "name": name,
        "objective": objective,
        "status": "PAUSED",
        "special_ad_categories": _json.dumps(special_ad_categories or []),
        "bid_strategy": bid_strategy,
    }
    if daily_budget_cents:
        payload["daily_budget"] = str(daily_budget_cents)
    result = await _post(f"/{acc_id}/campaigns", payload)
    return result["id"]

async def create_adset(acc_id: str, campaign_id: str, name: str, targeting: dict,
                       daily_budget_cents: int | None, bid_strategy: str,
                       bid_amount_cents: int | None, optimization_goal: str,
                       app_id: str | None = None, app_url: str | None = None,
                       custom_event_type: str | None = None) -> str:
    import json as _json
    promoted_object = {}
    if app_id:
        promoted_object["application_id"] = app_id
    if app_url:
        promoted_object["object_store_url"] = app_url
    if custom_event_type:
        promoted_object["custom_event_type"] = custom_event_type
    payload = {
        "name": name,
        "campaign_id": campaign_id,
        "targeting": _json.dumps(targeting),
        "billing_event": "IMPRESSIONS",
        "optimization_goal": optimization_goal,
        "status": "PAUSED",
    }
    if daily_budget_cents:
        payload["daily_budget"] = str(daily_budget_cents)
    if bid_amount_cents:
        payload["bid_amount"] = str(bid_amount_cents)
    if promoted_object:
        payload["promoted_object"] = _json.dumps(promoted_object)
    result = await _post(f"/{acc_id}/adsets", payload)
    return result["id"]

async def create_adcreative(acc_id: str, name: str, page_id: str,
                            image_hash: str | None, video_id: str | None,
                            message: str, link: str, headline: str) -> str:
    story = {
        "link_data" if not video_id else "video_data": {
            "message": message,
            "link": link,
            "name": headline,
            **({"image_hash": image_hash} if image_hash else {}),
            **({"video_id": video_id} if video_id else {}),
        },
        "page_id": page_id,
    }
    payload = {
        "name": name,
        "object_story_spec": str(story).replace("'", '"'),
    }
    result = await _post(f"/{acc_id}/adcreatives", payload)
    return result["id"]

async def create_ad(acc_id: str, adset_id: str, name: str, creative_id: str) -> str:
    payload = {
        "name": name,
        "adset_id": adset_id,
        "creative": f'{{"creative_id":"{creative_id}"}}',
        "status": "PAUSED",
    }
    result = await _post(f"/{acc_id}/ads", payload)
    return result["id"]
