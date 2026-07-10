# FB Auto Camp — Claude Instructions

## Project Overview

Web tool tự động tạo Facebook Ads campaign qua Meta Marketing API.
Mục tiêu: người dùng config template 1 lần, bấm nút → camp lên tự động.

## Stack

- **Backend:** FastAPI (Python) — `main.py`
- **Frontend:** Vanilla JS + HTML — `frontend/`
- **API:** Meta Marketing API v22+
- **Auth:** Access Token lưu trong `.env` (KHÔNG đọc file này)

## Cấu trúc dự kiến

```
fb-auto-camp/
├── main.py                  # FastAPI entry point
├── routers/                 # API routes theo module
│   ├── creative.py
│   ├── templates.py
│   ├── campaign.py
│   └── auth.py
├── services/                # Business logic
│   ├── meta_api.py          # Wrapper Meta Marketing API
│   └── campaign_builder.py  # Logic build campaign từ template
├── models/                  # Pydantic schemas
├── frontend/
│   ├── index.html
│   ├── js/
│   └── css/
└── .env                     # KHÔNG ĐỌC
```

## Core Features

1. **Creative Manager** — upload ảnh/video, gán tên, quản lý thư viện
2. **Template APP** — package name, app ID, FB page ID
3. **Template TARGET** — country, gender, age range, language, budget (CBO/ABO)
4. **Template AD** — headlines, primary text, số lượng creative dùng
5. **Package** — bundle APP + TARGET + AD để tái sử dụng
6. **Campaign Builder** — chọn package → preview → tạo campaign

## Meta API Flow

```
Campaign (objective, budget CBO)
└── Ad Set (targeting, budget ABO, schedule)
    └── Ad (creative, copy)
```

API version hiện tại: **v22.0**

## Conventions

- Route prefix: `/api/v1/`
- Response format: `{ "success": bool, "data": ..., "error": str | null }`
- Mọi call Meta API đều qua `services/meta_api.py`, không gọi thẳng từ router
- Frontend fetch API bằng Vanilla JS, không dùng framework

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# App tại http://localhost:8000
```

## Security

- `.env` chứa `FB_ACCESS_TOKEN`, `FB_APP_ID`, `FB_APP_SECRET` — KHÔNG BAO GIỜ đọc hay log
- Token phải là System User token (không expire)
