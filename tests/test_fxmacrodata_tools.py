from unittest.mock import MagicMock, patch

import pytest

from server import (
    get_fxmacrodata_calendar,
    get_fxmacrodata_catalogue,
    get_fxmacrodata_latest_announcements,
)

PLACEHOLDER_KEY = "test-placeholder-key"


def _fake_urlopen(body: bytes = b'{"data": []}') -> MagicMock:
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    return MagicMock(return_value=response)


@pytest.mark.asyncio
async def test_fxmacrodata_key_is_sent_as_header_not_in_url(monkeypatch):
    monkeypatch.setenv("FXMD_API_KEY", PLACEHOLDER_KEY)
    urlopen = _fake_urlopen()
    with patch("server.urllib.request.urlopen", urlopen):
        result = await get_fxmacrodata_calendar("USD", start_date="2026-01-01")

    assert result == '{"data": []}'
    request = urlopen.call_args.args[0]
    assert request.full_url == (
        "https://api.fxmacrodata.com/v1/calendar/usd?start_date=2026-01-01"
    )
    assert request.get_header("X-api-key") == PLACEHOLDER_KEY
    assert PLACEHOLDER_KEY not in request.full_url


@pytest.mark.asyncio
async def test_fxmacrodata_without_key_sends_no_auth_header(monkeypatch):
    monkeypatch.delenv("FXMD_API_KEY", raising=False)
    urlopen = _fake_urlopen()
    with patch("server.urllib.request.urlopen", urlopen):
        await get_fxmacrodata_catalogue("USD")
        await get_fxmacrodata_latest_announcements("usd")

    first, second = (call.args[0] for call in urlopen.call_args_list)
    assert first.full_url == "https://api.fxmacrodata.com/v1/data_catalogue/usd"
    assert second.full_url == "https://api.fxmacrodata.com/v1/announcements/usd/latest"
    assert first.get_header("X-api-key") is None
    assert second.get_header("X-api-key") is None
