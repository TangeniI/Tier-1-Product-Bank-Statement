from app.normalize import parse_amount, parse_date


def test_parse_amount_basic():
    assert parse_amount("45.50") == 4550
    assert parse_amount("£1,234.56") == 123456
    assert parse_amount("2,000.00") == 200000
    assert parse_amount("0.45") == 45


def test_parse_amount_negatives():
    assert parse_amount("(50.00)") == -5000
    assert parse_amount("-12.30") == -1230
    assert parse_amount("45.00 DR") == -4500
    assert parse_amount("45.00 CR") == 4500


def test_parse_amount_non_numbers():
    assert parse_amount("") is None
    assert parse_amount("ATM withdrawal") is None
    assert parse_amount(None) is None


def test_parse_date_uk_formats():
    fmts = ("%d %b %Y", "%d/%m/%Y")
    assert parse_date("02 Apr 2026", fmts) == "2026-04-02"
    assert parse_date("02/04/2026", fmts) == "2026-04-02"
    assert parse_date("not a date", fmts) is None
