from app.services.merge import merge_text, spreadsheet_id


def test_merge_is_case_insensitive_and_missing_values_are_empty():
    assert merge_text("Hi {{ First_Name }} from {{company}} {{missing}}", {"first_name": "Asha", "Company": "Acme"}) == "Hi Asha from Acme "


def test_spreadsheet_id_accepts_url_or_id():
    assert spreadsheet_id("https://docs.google.com/spreadsheets/d/abc-123/edit") == "abc-123"
    assert spreadsheet_id("abc-123") == "abc-123"
