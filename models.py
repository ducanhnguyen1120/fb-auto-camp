from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, func
from database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    acc_id = Column(String, nullable=False, unique=True)
    note = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())

class TemplateApp(Base):
    __tablename__ = "templates_app"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    pkg = Column(String, default="")
    app_id = Column(String, default="")
    dev_id = Column(String, default="")
    page_id = Column(String, default="")
    app_url = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())

class TemplateTarget(Base):
    __tablename__ = "templates_target"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(JSON, default=list)
    lang = Column(JSON, default=list)
    gender = Column(String, default="all")
    age_min = Column(Integer, default=18)
    age_max = Column(Integer, default=45)
    budget_type = Column(String, default="CBO")
    budget = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())

class TemplateAd(Base):
    __tablename__ = "templates_ad"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    headlines = Column(Text, default="")
    text = Column(Text, default="")
    cr_count = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    app_id = Column(Integer)
    target_id = Column(Integer)
    ad_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class CreativeMetaAsset(Base):
    __tablename__ = "creative_meta_assets"
    id = Column(Integer, primary_key=True, index=True)
    creative_id = Column(Integer, nullable=False, index=True)
    acc_id = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)   # "video" | "image"
    meta_id = Column(String, nullable=False)       # video_id or image_hash
    created_at = Column(DateTime, server_default=func.now())

class Creative(Base):
    __tablename__ = "creatives"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    size = Column(String, default="")
    type = Column(String, default="image")
    app = Column(String, default="")
    style = Column(String, default="")
    target = Column(String, default="")
    custom = Column(String, default="")
    file_path = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())
