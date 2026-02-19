import httpx
from app.core.config import settings

RESEND_API_URL = "https://api.resend.com/emails"

async def send_email(to: str, subject: str, html: str):
    if not settings.RESEND_API_KEY or not settings.RESEND_FROM:
        return False

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": settings.RESEND_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(RESEND_API_URL, headers=headers, json=payload)
        return resp.status_code in (200, 201)
