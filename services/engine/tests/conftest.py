"""Shared pytest fixtures: build the synthetic statement PDF once per session."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))
sys.path.insert(0, str(ENGINE_ROOT / "scripts"))


@pytest.fixture(scope="session")
def barclays_pdf_bytes(tmp_path_factory) -> bytes:
    from make_fixture import build_pdf

    out = tmp_path_factory.mktemp("fixtures") / "barclays_sample.pdf"
    build_pdf(out)
    return out.read_bytes()


@pytest.fixture(scope="session")
def barclays_yearless_pdf_bytes(tmp_path_factory) -> bytes:
    from make_fixture import build_yearless_pdf

    out = tmp_path_factory.mktemp("fixtures") / "barclays_yearless.pdf"
    build_yearless_pdf(out)
    return out.read_bytes()


@pytest.fixture(scope="session")
def barclays_boundary_pdf_bytes(tmp_path_factory) -> bytes:
    from make_fixture import build_boundary_pdf

    out = tmp_path_factory.mktemp("fixtures") / "barclays_boundary.pdf"
    build_boundary_pdf(out)
    return out.read_bytes()
