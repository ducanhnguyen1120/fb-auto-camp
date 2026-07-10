# FB Auto Camp

Web tool để tự động lên campaign Facebook Ads trên nhiều kênh.

## Tính năng

- Upload và quản lý Creative
- Template APP (package name, app ID, pages)
- Template TARGET (country, gender, age, language, budget CBO/ABO)
- Template AD (headlines, primary text, số lượng CR)
- Package: bundle các template lại để tái sử dụng
- Lên campaign tự động qua Meta Marketing API

## Stack

- Frontend: HTML / Vanilla JS (hoặc React sau)
- Backend: FastAPI (Python)
- API: Meta Marketing API v19+

## Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
