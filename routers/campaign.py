from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Package, TemplateApp, TemplateTarget, TemplateAd, Creative
from services.campaign_builder import build_campaign

router = APIRouter(prefix="/api/v1/campaign", tags=["campaign"])

class LaunchRequest(BaseModel):
    acc_id: str
    package_ids: list[int]
    creative_ids: list[int]
    campaign_names: list[str]        # one per package, pre-built by FE
    cr_per_ad: int = 1
    budget_type: str = "CBO"
    daily_budget_usd: float = 0
    bid_strategy: str = "lowest_cost"
    bid_amount_usd: Optional[float] = None
    objective: str = "app_installs"

@router.post("/launch")
async def launch(body: LaunchRequest, db: Session = Depends(get_db)):
    creatives = db.query(Creative).filter(Creative.id.in_(body.creative_ids)).all()
    cr_list = [{"id": c.id, "name": c.name, "type": c.type, "filePath": c.file_path} for c in creatives]

    results = []
    errors = []

    for idx, pkg_id in enumerate(body.package_ids):
        pkg = db.query(Package).filter(Package.id == pkg_id).first()
        if not pkg:
            errors.append(f"Package {pkg_id} không tồn tại")
            continue

        app_tpl = db.query(TemplateApp).filter(TemplateApp.id == pkg.app_id).first()
        tgt_tpl = db.query(TemplateTarget).filter(TemplateTarget.id == pkg.target_id).first()
        ad_tpl = db.query(TemplateAd).filter(TemplateAd.id == pkg.ad_id).first()

        if not app_tpl or not tgt_tpl or not ad_tpl:
            errors.append(f"Package {pkg.name}: thiếu template")
            continue

        camp_name = body.campaign_names[idx] if idx < len(body.campaign_names) else pkg.name

        result = await build_campaign(
            acc_id=body.acc_id,
            campaign_name=camp_name,
            package={"id": pkg.id, "name": pkg.name},
            app_tpl={"pageId": app_tpl.page_id, "appId": app_tpl.app_id, "pkg": app_tpl.pkg, "appUrl": app_tpl.app_url},
            target_tpl={"country": tgt_tpl.country, "lang": tgt_tpl.lang, "gender": tgt_tpl.gender,
                        "ageMin": tgt_tpl.age_min, "ageMax": tgt_tpl.age_max},
            ad_tpl={"headlines": ad_tpl.headlines, "text": ad_tpl.text},
            creatives=cr_list,
            cr_per_ad=body.cr_per_ad,
            budget_type=body.budget_type,
            daily_budget_usd=body.daily_budget_usd,
            bid_strategy=body.bid_strategy,
            bid_amount_usd=body.bid_amount_usd,
            objective=body.objective,
            db=db,
        )

        results.append({
            "package": pkg.name,
            "campaignId": result.campaign_id,
            "adsetIds": result.adset_ids,
            "adIds": result.ad_ids,
            "errors": result.errors,
        })
        errors.extend(result.errors)

    ok = all(r["campaignId"] for r in results)
    return {
        "success": ok,
        "data": results,
        "error": "; ".join(errors) if errors else None,
    }
