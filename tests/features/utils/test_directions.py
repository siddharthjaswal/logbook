"""Tests for the directions-link parser (no network: full /dir/ URLs skip expansion)."""
import pytest
from app.features.utils.router import resolve_directions_link

EXPANDED = (
    "https://www.google.com/maps/dir/"
    "Josep+Tarradellas+Barcelona-El+Prat+Airport,+08820+El+Prat+de+Llobregat,+Barcelona,+Spain/"
    "Pla%C3%A7a+de+Catalunya,+Eixample,+08002+Barcelona,+Spain/"
    "@41.338723,2.0289111,12z/data=!3m1!4b1!4m13!4m12!1m5!1m1!1s0x12a49e64847c8ea5:0x0"
    "!2m2!1d2.0800095!2d41.2983405!1m5!1m1!1s0x12a4a2f1602b4819:0x0!2m2!1d2.1700471!2d41.3870154"
)


async def test_parses_origin_and_destination():
    res = await resolve_directions_link(url=EXPANDED, current_user=None)
    assert res["origin"]["lat"] == pytest.approx(41.2983405)
    assert res["origin"]["lng"] == pytest.approx(2.0800095)
    assert "Airport" in res["origin"]["name"]
    assert res["destination"]["lat"] == pytest.approx(41.3870154)
    assert "Catalunya" in res["destination"]["name"]
    assert res["waypoints"] == []


async def test_extracts_travel_mode():
    url = EXPANDED + "!3e3"  # transit
    res = await resolve_directions_link(url=url, current_user=None)
    assert res["mode"] == "train"
    assert res["google_mode"] == "transit"


async def test_rejects_non_directions_link():
    res = await resolve_directions_link(
        url="https://www.google.com/maps/place/Foo/@41.0,2.0,12z", current_user=None
    )
    assert res.get("error")
