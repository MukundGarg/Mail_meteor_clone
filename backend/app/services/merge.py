import html
import re

TOKEN = re.compile(r"{{\s*([^{}]+?)\s*}}")


def merge_text(value: str, data: dict) -> str:
    normalized = {str(key).strip().lower(): val for key, val in data.items()}
    return TOKEN.sub(lambda match: str(normalized.get(match.group(1).strip().lower(), "")), value)


def text_to_html(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def spreadsheet_id(value: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", value)
    return match.group(1) if match else value.strip()

