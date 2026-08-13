import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from .database import SessionLocal
from .models import Campaign, CampaignEvent, CampaignStatus, Recipient, RecipientStatus, User
from .services.google import send_message, thread_has_reply, update_sheet_status
from .services.merge import merge_text, text_to_html


def utcnow() -> datetime:
    return datetime.now(UTC)


async def _sync_reply(user: User, recipient: Recipient) -> bool:
    if not recipient.gmail_thread_id or recipient.replied_at:
        return False
    replied = await asyncio.to_thread(thread_has_reply, user, recipient.gmail_thread_id, recipient.email)
    if replied:
        recipient.replied_at = utcnow()
        recipient.status = RecipientStatus.REPLIED
    return replied


async def sync_recent_replies(limit: int = 100) -> int:
    cutoff = utcnow() - timedelta(days=30)
    found = 0
    async with SessionLocal() as db:
        recipients = (
            await db.execute(
                select(Recipient)
                .where(
                    Recipient.gmail_thread_id.is_not(None),
                    Recipient.replied_at.is_(None),
                    Recipient.last_sent_at >= cutoff,
                )
                .options(selectinload(Recipient.campaign))
                .limit(limit)
            )
        ).scalars().all()
        users: dict[str, User] = {}
        for recipient in recipients:
            campaign = recipient.campaign
            user = users.get(campaign.user_id) or await db.get(User, campaign.user_id)
            if not user:
                continue
            users[campaign.user_id] = user
            try:
                if await _sync_reply(user, recipient):
                    campaign.replied_count += 1
                    db.add(
                        CampaignEvent(
                            campaign_id=campaign.id,
                            recipient_id=recipient.id,
                            kind="REPLIED",
                        )
                    )
                    found += 1
                    if campaign.spreadsheet_id and campaign.sheet_name and recipient.data.get("__row_number"):
                        await asyncio.to_thread(
                            update_sheet_status,
                            user,
                            campaign.spreadsheet_id,
                            campaign.sheet_name,
                            int(recipient.data["__row_number"]),
                            "REPLIED",
                            recipient.last_sent_at.isoformat() if recipient.last_sent_at else "",
                            recipient.replied_at.isoformat(),
                        )
            except Exception:
                continue
        await db.commit()
    return found


async def process_due(limit: int = 25) -> dict:
    replies = await sync_recent_replies()
    processed: list[dict] = []
    async with SessionLocal() as db:
        campaigns = (
            await db.execute(
                select(Campaign)
                .where(
                    Campaign.status.in_([CampaignStatus.SCHEDULED, CampaignStatus.RUNNING]),
                    Campaign.scheduled_at <= utcnow(),
                )
                .options(selectinload(Campaign.steps))
                .order_by(Campaign.scheduled_at)
                .limit(10)
            )
        ).scalars().all()

        for campaign in campaigns:
            campaign.status = CampaignStatus.RUNNING
            user = await db.get(User, campaign.user_id)
            if not user:
                continue
            recipients = (
                await db.execute(
                    select(Recipient)
                    .where(
                        Recipient.campaign_id == campaign.id,
                        Recipient.status.in_([RecipientStatus.READY, RecipientStatus.ACTIVE]),
                        Recipient.next_send_at <= utcnow(),
                    )
                    .order_by(Recipient.next_send_at)
                    .limit(limit)
                )
            ).scalars().all()
            steps = sorted((step for step in campaign.steps if step.enabled), key=lambda item: item.position)

            for recipient in recipients:
                try:
                    if await _sync_reply(user, recipient):
                        campaign.replied_count += 1
                        db.add(CampaignEvent(campaign_id=campaign.id, recipient_id=recipient.id, kind="REPLIED"))
                        processed.append({"recipient": recipient.email, "status": "REPLIED"})
                        if campaign.spreadsheet_id and campaign.sheet_name and recipient.data.get("__row_number"):
                            await asyncio.to_thread(
                                update_sheet_status,
                                user,
                                campaign.spreadsheet_id,
                                campaign.sheet_name,
                                int(recipient.data["__row_number"]),
                                "REPLIED",
                                recipient.last_sent_at.isoformat() if recipient.last_sent_at else "",
                                recipient.replied_at.isoformat(),
                            )
                        continue

                    next_step = recipient.current_step + 1
                    if next_step == 0:
                        subject, body = campaign.subject, campaign.body
                    elif next_step <= len(steps):
                        step = steps[next_step - 1]
                        subject, body = step.subject or campaign.subject, step.body
                    else:
                        recipient.status = RecipientStatus.COMPLETED
                        continue

                    merged = {**recipient.data, "email": recipient.email, "first_name": recipient.first_name or "", "last_name": recipient.last_name or "", "company": recipient.company or ""}
                    result, rfc_id = await asyncio.to_thread(
                        send_message,
                        user,
                        recipient.email,
                        merge_text(subject, merged),
                        text_to_html(merge_text(body, merged)),
                        thread_id=recipient.gmail_thread_id,
                        in_reply_to=recipient.rfc_message_id,
                    )
                    sent_at = utcnow()
                    recipient.current_step = next_step
                    recipient.last_sent_at = sent_at
                    recipient.gmail_message_id = result.get("id")
                    recipient.gmail_thread_id = result.get("threadId")
                    recipient.rfc_message_id = rfc_id
                    recipient.attempts += 1
                    recipient.error = None
                    campaign.sent_count += 1
                    if next_step < len(steps):
                        delay = steps[next_step].delay_days
                        recipient.next_send_at = sent_at + timedelta(days=delay)
                        recipient.status = RecipientStatus.ACTIVE
                    else:
                        recipient.next_send_at = None
                        recipient.status = RecipientStatus.COMPLETED
                    db.add(CampaignEvent(campaign_id=campaign.id, recipient_id=recipient.id, kind="SENT", detail={"step": next_step}))
                    processed.append({"recipient": recipient.email, "status": "SENT", "step": next_step})
                    if campaign.spreadsheet_id and campaign.sheet_name and recipient.data.get("__row_number"):
                        await asyncio.to_thread(
                            update_sheet_status,
                            user,
                            campaign.spreadsheet_id,
                            campaign.sheet_name,
                            int(recipient.data["__row_number"]),
                            "SENT" if recipient.status == RecipientStatus.COMPLETED else "FOLLOW_UP_SCHEDULED",
                            sent_at.isoformat(),
                            "",
                        )
                    await db.commit()
                    await asyncio.sleep(campaign.send_interval_seconds)
                except Exception as exc:  # provider errors are recorded for retry
                    recipient.attempts += 1
                    recipient.error = str(exc)[:1000]
                    if recipient.attempts >= 3:
                        recipient.status = RecipientStatus.FAILED
                        campaign.failed_count += 1
                    else:
                        recipient.next_send_at = utcnow() + timedelta(minutes=15)
                    processed.append({"recipient": recipient.email, "status": "FAILED"})
                    await db.commit()

            remaining = await db.scalar(
                select(func.count()).select_from(Recipient).where(
                    Recipient.campaign_id == campaign.id,
                    Recipient.status.in_([RecipientStatus.READY, RecipientStatus.ACTIVE]),
                )
            )
            if not remaining:
                campaign.status = CampaignStatus.COMPLETED
            await db.commit()
    return {"processed": len(processed), "replies_found": replies, "results": processed}


async def run_forever(interval_seconds: int = 30) -> None:
    while True:
        await process_due()
        await asyncio.sleep(interval_seconds)
