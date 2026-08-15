import csv
import io
import secrets
from datetime import UTC

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import settings
from .database import get_db
from .dependencies import current_user
from .models import Campaign, CampaignEvent, CampaignStatus, Recipient, SequenceStep, Template, User
from .schemas import CampaignCreate, SheetPreview, TemplateCreate, TestEmailInput
from .security import encrypt, sign_session
from .services.google import oauth_flow, read_sheet, send_message
from .services.merge import merge_text, spreadsheet_id, text_to_html
from .worker import process_due

router = APIRouter(prefix="/api/v1")


def campaign_json(campaign: Campaign) -> dict:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "subject": campaign.subject,
        "body": campaign.body,
        "source": campaign.source,
        "status": campaign.status.value,
        "scheduled_at": campaign.scheduled_at,
        "total_count": campaign.total_count,
        "sent_count": campaign.sent_count,
        "replied_count": campaign.replied_count,
        "failed_count": campaign.failed_count,
        "created_at": campaign.created_at,
    }


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@router.get("/auth/google/start")
async def google_start(request: Request) -> RedirectResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    state = secrets.token_urlsafe(32)

    flow = oauth_flow()
    url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
    )

    response = RedirectResponse(url)

    response.set_cookie(
        "oauth_state",
        state,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=600,
    )

    response.set_cookie(
        "oauth_code_verifier",
        flow.code_verifier,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=600,
    )

    return response


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    state = request.query_params.get("state")

    if not state or state != request.cookies.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    code_verifier = request.cookies.get("oauth_code_verifier")

    if not code_verifier:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth code verifier",
        )

    flow = oauth_flow(
        state=state,
        code_verifier=code_verifier,
    )

    callback_url = f"{settings.google_redirect_uri}?{request.url.query}"

    flow.fetch_token(
        authorization_response=callback_url,
    )

    if not flow.credentials.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Google did not return a refresh token",
        )

    oauth = build(
        "oauth2",
        "v2",
        credentials=flow.credentials,
        cache_discovery=False,
    )

    profile = oauth.userinfo().get().execute()

    user = await db.scalar(
        select(User).where(User.email == profile["email"])
    )

    if not user:
        user = User(
            email=profile["email"],
            name=profile.get("name"),
            google_refresh_token=encrypt(
                flow.credentials.refresh_token
            ),
        )
        db.add(user)
    else:
        user.name = profile.get("name")
        user.google_refresh_token = encrypt(
            flow.credentials.refresh_token
        )

    await db.commit()
    await db.refresh(user)

    response = RedirectResponse(f"{settings.frontend_url}/")

    response.set_cookie(
        "mm_session",
        sign_session(user.id),
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=30 * 24 * 3600,
    )

    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_code_verifier")

    return response

    # ...rest of your existing callback code...


@router.get("/auth/me")
async def me(user: User = Depends(current_user)) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}


@router.post("/auth/logout")
async def logout() -> Response:
    response = Response(status_code=204)
    response.delete_cookie("mm_session")
    return response


@router.get("/campaigns")
async def list_campaigns(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> list[dict]:
    campaigns = (await db.execute(select(Campaign).where(Campaign.user_id == user.id).order_by(Campaign.created_at.desc()))).scalars().all()
    return [campaign_json(item) for item in campaigns]


@router.post("/campaigns", status_code=201)
async def create_campaign(payload: CampaignCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> dict:
    unique = {str(contact.email).casefold(): contact for contact in payload.contacts}
    campaign = Campaign(
        user_id=user.id,
        name=payload.name,
        subject=payload.subject,
        body=payload.body,
        source=payload.source,
        spreadsheet_id=spreadsheet_id(payload.spreadsheet_id) if payload.spreadsheet_id else None,
        sheet_name=payload.sheet_name,
        status=CampaignStatus.SCHEDULED,
        scheduled_at=payload.scheduled_at.astimezone(UTC),
        send_interval_seconds=payload.send_interval_seconds,
        total_count=len(unique),
    )
    db.add(campaign)
    await db.flush()
    for contact in unique.values():
        merged = {**contact.data, "first_name": contact.first_name or "", "last_name": contact.last_name or "", "company": contact.company or ""}
        db.add(Recipient(campaign_id=campaign.id, email=str(contact.email), first_name=contact.first_name, last_name=contact.last_name, company=contact.company, data=merged, next_send_at=campaign.scheduled_at))
    for index, step in enumerate(payload.followups, start=1):
        db.add(SequenceStep(campaign_id=campaign.id, position=index, delay_days=step.delay_days, subject=step.subject, body=step.body))
    db.add(CampaignEvent(campaign_id=campaign.id, kind="CREATED", detail={"recipients": len(unique)}))
    await db.commit()
    return {"id": campaign.id}


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> dict:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id).options(selectinload(Campaign.recipients), selectinload(Campaign.steps)))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    result = campaign_json(campaign)
    result["recipients"] = [{"id": r.id, "email": r.email, "first_name": r.first_name, "last_name": r.last_name, "company": r.company, "status": r.status.value, "current_step": r.current_step, "last_sent_at": r.last_sent_at, "replied_at": r.replied_at, "error": r.error} for r in campaign.recipients]
    result["followups"] = [{"id": s.id, "position": s.position, "delay_days": s.delay_days, "subject": s.subject, "body": s.body} for s in sorted(campaign.steps, key=lambda x: x.position)]
    return result


@router.post("/campaigns/{campaign_id}/pause", status_code=204)
async def pause_campaign(campaign_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> Response:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    return Response(status_code=204)


@router.post("/campaigns/{campaign_id}/resume", status_code=204)
async def resume_campaign(campaign_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> Response:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = CampaignStatus.SCHEDULED
    await db.commit()
    return Response(status_code=204)


@router.post("/sheets/preview")
async def sheet_preview(payload: SheetPreview, user: User = Depends(current_user)) -> dict:
    rows = await __import__("asyncio").to_thread(read_sheet, user, spreadsheet_id(payload.sheet), payload.sheet_name)
    headers = [str(item) for item in (rows[0] if rows else [])]
    return {"spreadsheet_id": spreadsheet_id(payload.sheet), "headers": headers, "rows": [dict(zip(headers, row, strict=False)) for row in rows[1:201]], "total": max(0, len(rows) - 1)}


@router.post("/contacts/import-csv")
async def import_csv(file: UploadFile = File(...), user: User = Depends(current_user)) -> dict:
    del user
    content = (await file.read()).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(content)))
    return {"headers": list(rows[0].keys()) if rows else [], "rows": rows[:2000], "total": len(rows)}


@router.get("/contacts")
async def list_contacts(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (
        await db.execute(
            select(Recipient, Campaign.name)
            .join(Campaign, Campaign.id == Recipient.campaign_id)
            .where(Campaign.user_id == user.id)
            .order_by(Recipient.last_sent_at.desc(), Recipient.email)
        )
    ).all()
    seen: set[str] = set()
    contacts: list[dict] = []
    for recipient, campaign_name in rows:
        key = recipient.email.casefold()
        if key in seen:
            continue
        seen.add(key)
        contacts.append(
            {
                "id": recipient.id,
                "email": recipient.email,
                "first_name": recipient.first_name,
                "last_name": recipient.last_name,
                "company": recipient.company,
                "status": recipient.status.value,
                "current_step": recipient.current_step,
                "last_sent_at": recipient.last_sent_at,
                "replied_at": recipient.replied_at,
                "error": recipient.error,
                "campaign": campaign_name,
                "campaign_id": recipient.campaign_id,
            }
        )
    return contacts


@router.post("/messages/test")
async def test_message(payload: TestEmailInput, user: User = Depends(current_user)) -> dict:
    result, _ = await __import__("asyncio").to_thread(
        send_message,
        user,
        user.email,
        merge_text(payload.subject, payload.data),
        text_to_html(merge_text(payload.body, payload.data)),
    )
    return {"message_id": result.get("id"), "sent_to": user.email}


@router.get("/templates")
async def list_templates(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> list[dict]:
    items = (await db.execute(select(Template).where(Template.user_id == user.id).order_by(Template.created_at.desc()))).scalars().all()
    return [{"id": item.id, "name": item.name, "subject": item.subject, "body": item.body} for item in items]


@router.post("/templates", status_code=201)
async def create_template(payload: TemplateCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> dict:
    item = Template(user_id=user.id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}


@router.delete("/templates/{template_id}", status_code=204)
async def remove_template(template_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> Response:
    await db.execute(delete(Template).where(Template.id == template_id, Template.user_id == user.id))
    await db.commit()
    return Response(status_code=204)


@router.post("/cron/process")
async def cron_process(request: Request) -> dict:
    if request.headers.get("authorization") != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await process_due()
