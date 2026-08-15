import base64
import email.utils
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from ..config import settings
from ..models import User
from ..security import decrypt

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]


def oauth_flow(
    state: str | None = None,
    code_verifier: str | None = None,
) -> Flow:
    config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }

    return Flow.from_client_config(
        config,
        scopes=SCOPES,
        state=state,
        redirect_uri=settings.google_redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=code_verifier is None,
    )

def credentials_for(user: User) -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=decrypt(user.google_refresh_token),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def gmail_for(user: User):
    return build("gmail", "v1", credentials=credentials_for(user), cache_discovery=False)


def sheets_for(user: User):
    return build("sheets", "v4", credentials=credentials_for(user), cache_discovery=False)


def read_sheet(user: User, sheet_id: str, sheet_name: str) -> list[list[str]]:
    escaped_name = sheet_name.replace("'", "''")
    result = (
        sheets_for(user)
        .spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=f"'{escaped_name}'")
        .execute()
    )
    return result.get("values", [])


def send_message(
    user: User,
    to: str,
    subject: str,
    html_body: str,
    *,
    thread_id: str | None = None,
    in_reply_to: str | None = None,
) -> tuple[dict, str]:
    message = EmailMessage()
    message["To"] = to
    message["From"] = user.email
    message["Subject"] = subject.replace("\r", " ").replace("\n", " ")
    rfc_message_id = email.utils.make_msgid(domain="mailpilot.local")
    message["Message-ID"] = rfc_message_id
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to
    message.set_content("This message requires an HTML-capable email client.")
    message.add_alternative(html_body, subtype="html")
    payload: dict[str, str] = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
    if thread_id:
        payload["threadId"] = thread_id
    result = gmail_for(user).users().messages().send(userId="me", body=payload).execute()
    return result, rfc_message_id


def thread_has_reply(user: User, thread_id: str, recipient_email: str) -> bool:
    thread = gmail_for(user).users().threads().get(userId="me", id=thread_id, format="metadata").execute()
    recipient = recipient_email.casefold()
    for message in thread.get("messages", []):
        headers = {
            h["name"].casefold(): h["value"] for h in message.get("payload", {}).get("headers", [])
        }
        sender = headers.get("from", "").casefold()
        if recipient in sender and "SENT" not in message.get("labelIds", []):
            return True
    return False


def _column_letter(index: int) -> str:
    value = index + 1
    output = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        output = chr(65 + remainder) + output
    return output


def update_sheet_status(
    user: User,
    sheet_id: str,
    sheet_name: str,
    row_number: int,
    status: str,
    last_sent_at: str = "",
    replied_at: str = "",
) -> None:
    service = sheets_for(user).spreadsheets().values()
    escaped = sheet_name.replace("'", "''")
    header_result = service.get(spreadsheetId=sheet_id, range=f"'{escaped}'!1:1").execute()
    headers = [str(value) for value in (header_result.get("values") or [[]])[0]]
    required = ["MailPilot Status", "MailPilot Last Sent", "MailPilot Replied At"]
    if any(name not in headers for name in required):
        headers.extend(name for name in required if name not in headers)
        service.update(
            spreadsheetId=sheet_id,
            range=f"'{escaped}'!1:1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()
    indices = [headers.index(name) for name in required]
    start, end = min(indices), max(indices)
    values = [""] * (end - start + 1)
    values[indices[0] - start] = status
    values[indices[1] - start] = last_sent_at
    values[indices[2] - start] = replied_at
    service.update(
        spreadsheetId=sheet_id,
        range=f"'{escaped}'!{_column_letter(start)}{row_number}:{_column_letter(end)}{row_number}",
        valueInputOption="RAW",
        body={"values": [values]},
    ).execute()
