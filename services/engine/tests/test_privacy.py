"""Privacy guardrail: extraction must process statements entirely in memory and
never write them to disk. This makes the "we never store your statements" claim
an enforced, tested property rather than a promise."""
import builtins

from make_fixture import build_pdf

from app.pipeline import extract


def test_extraction_opens_nothing_for_writing(tmp_path, monkeypatch):
    pdf = tmp_path / "statement.pdf"
    build_pdf(pdf)  # built before we install the spy
    data = pdf.read_bytes()

    real_open = builtins.open
    write_opens = []

    def spy_open(file, mode="r", *args, **kwargs):
        if any(flag in str(mode) for flag in ("w", "a", "x", "+")):
            write_opens.append((str(file), mode))
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy_open)
    result = extract(data)

    assert len(result.rows) > 0  # sanity: it actually ran
    assert write_opens == [], f"extraction wrote to disk: {write_opens}"
