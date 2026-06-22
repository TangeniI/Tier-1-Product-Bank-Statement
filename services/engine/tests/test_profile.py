"""Finding C: profile matching must use bank-identity signals, not a stray
mention of a bank's name in a transaction line."""
from app.profile_loader import match_profile


def test_real_barclays_statement_matches():
    text = "Barclays Bank UK PLC\nStatement of account\nVisit barclays.co.uk"
    assert match_profile(text).name == "barclays"


def test_stray_mention_does_not_misclassify():
    # A Monzo statement that merely references a payment to Barclays must not be
    # classified as a Barclays statement — it falls back to generic.
    text = "Monzo Bank Limited\n02 Apr  Faster payment to Barclays  -50.00"
    assert match_profile(text).name == "generic"
