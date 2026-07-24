from dataclasses import dataclass, field
from typing import Optional
from sqlalchemy.orm import Session
from models import CreativeMetaAsset
from services import meta_api

OBJECTIVE_MAP = {
    "app_installs": "OUTCOME_APP_PROMOTION",
    "value_ad_impression": "OUTCOME_APP_PROMOTION",
    "conversions": "CONVERSIONS",
    "reach": "REACH",
    "link_clicks": "LINK_CLICKS",
}

OPTIMIZATION_GOAL_MAP = {
    "app_installs": "APP_INSTALLS",
    "value_ad_impression": "APP_INSTALLS",
}

# custom_event_type for VALUE optimization
CUSTOM_EVENT_MAP = {
    "value_ad_impression": "AD_IMPRESSION",
}

BID_STRATEGY_MAP = {
    "lowest_cost": "LOWEST_COST_WITHOUT_CAP",
    "cost_cap": "COST_CAP",
    "bid_cap": "LOWEST_COST_WITH_BID_CAP",
    "target_cost": "TARGET_COST",
}

@dataclass
class LaunchResult:
    campaign_id: str
    adset_ids: list[str] = field(default_factory=list)
    ad_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

async def _get_or_raise_meta_id(creative: dict, acc_id: str, db: Session) -> tuple[str, str]:
    """Return (asset_type, meta_id). Raises if not uploaded yet."""
    row = db.query(CreativeMetaAsset).filter(
        CreativeMetaAsset.creative_id == creative["id"],
        CreativeMetaAsset.acc_id == acc_id,
    ).first()
    if not row:
        raise RuntimeError(
            f"Creative '{creative['name']}' chưa được upload lên account {acc_id}. "
            "Upload creative trước khi launch."
        )
    return row.asset_type, row.meta_id

async def build_campaign(
    acc_id: str,
    campaign_name: str,
    package: dict,
    app_tpl: dict,
    target_tpl: dict,
    ad_tpl: dict,
    creatives: list[dict],
    cr_per_ad: int,
    budget_type: str,
    daily_budget_usd: float,
    bid_strategy: str,
    bid_amount_usd: Optional[float],
    objective: str = "app_installs",
    db: Session = None,
) -> LaunchResult:
    errors = []
    ad_ids = []
    adset_ids = []

    budget_cents = int(daily_budget_usd * 100) if daily_budget_usd else None
    bid_cents = int(bid_amount_usd * 100) if bid_amount_usd else None
    meta_obj = OBJECTIVE_MAP.get(objective, "APP_INSTALLS")
    meta_bid = BID_STRATEGY_MAP.get(bid_strategy, "LOWEST_COST_WITHOUT_CAP")
    cbo = budget_type.upper() == "CBO"
    page_id = app_tpl.get("pageId", "")
    targeting = _build_targeting(target_tpl)

    try:
        camp_id = await meta_api.create_campaign(
            acc_id=acc_id,
            name=campaign_name,
            objective=meta_obj,
            daily_budget_cents=budget_cents if cbo else None,
            special_ad_categories=[],
            bid_strategy=meta_bid,
        )
    except Exception as e:
        errors.append(f"Tạo campaign thất bại: {e}")
        return LaunchResult(campaign_id="", errors=errors)

    batches = [creatives[i:i+cr_per_ad] for i in range(0, len(creatives), cr_per_ad)]
    headlines = [h for h in (ad_tpl.get("headlines") or "").split("\n") if h.strip()]
    primary_text = ad_tpl.get("text", "")

    for idx, batch in enumerate(batches):
        adset_name = f"{campaign_name}_AdSet_{idx+1:02d}"
        try:
            adset_id = await meta_api.create_adset(
                acc_id=acc_id,
                campaign_id=camp_id,
                name=adset_name,
                targeting=targeting,
                daily_budget_cents=budget_cents if not cbo else None,
                bid_strategy=meta_bid,
                bid_amount_cents=bid_cents,
                optimization_goal=OPTIMIZATION_GOAL_MAP.get(objective, "APP_INSTALLS"),
                app_id=app_tpl.get("appId"),
                app_url=app_tpl.get("appUrl"),
                custom_event_type=CUSTOM_EVENT_MAP.get(objective),
            )
            adset_ids.append(adset_id)
        except Exception as e:
            errors.append(f"AdSet {idx+1}: {e}")
            continue

        for cr_idx, cr in enumerate(batch):
            try:
                asset_type, meta_id = await _get_or_raise_meta_id(cr, acc_id, db)
                image_hash = meta_id if asset_type == "image" else None
                video_id = meta_id if asset_type == "video" else None

                app_url = app_tpl.get("appUrl") or "https://fb.me/"
                creative_id = await meta_api.create_adcreative(
                    acc_id=acc_id,
                    name=f"{campaign_name}_Creative_{idx+1:02d}_{cr_idx+1:02d}",
                    page_id=page_id,
                    image_hash=image_hash,
                    video_id=video_id,
                    message=primary_text,
                    link=app_url,
                    headline=headlines[cr_idx % len(headlines)] if headlines else cr.get("name", ""),
                )
                ad_id = await meta_api.create_ad(
                    acc_id=acc_id,
                    adset_id=adset_id,
                    name=f"{campaign_name}_Ad_{idx+1:02d}_{cr_idx+1:02d}",
                    creative_id=creative_id,
                )
                ad_ids.append(ad_id)
            except Exception as e:
                errors.append(f"Ad {idx+1}-{cr_idx+1} ({cr.get('name','')}): {e}")

    return LaunchResult(campaign_id=camp_id, adset_ids=adset_ids, ad_ids=ad_ids, errors=errors)

def _build_targeting(target_tpl: dict) -> dict:
    countries = target_tpl.get("country") or []
    langs = target_tpl.get("lang") or []
    gender_map = {"male": [1], "female": [2], "all": []}
    genders = gender_map.get(target_tpl.get("gender", "all"), [])
    t = {
        "geo_locations": {"countries": countries},
        "age_min": target_tpl.get("ageMin", 18),
        "age_max": target_tpl.get("ageMax", 65),
    }
    if genders:
        t["genders"] = genders
    if langs:
        t["locales"] = langs
    return t
