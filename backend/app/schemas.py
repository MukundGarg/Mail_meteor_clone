from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactInput(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    data: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class FollowupInput(BaseModel):
    delay_days: int = Field(default=2, ge=1, le=30)
    subject: str | None = Field(default=None, max_length=500)
    body: str = Field(min_length=1, max_length=20_000)


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=20_000)
    contacts: list[ContactInput] = Field(min_length=1, max_length=2000)
    followups: list[FollowupInput] = Field(default_factory=list, max_length=4)
    scheduled_at: datetime
    send_interval_seconds: int = Field(default=45, ge=15, le=3600)
    source: str = "MANUAL"
    spreadsheet_id: str | None = None
    sheet_name: str | None = None


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=20_000)


class TestEmailInput(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=20_000)
    data: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class SheetPreview(BaseModel):
    sheet: str
    sheet_name: str = "Sheet1"
