"""WebSocket broadcast unit tests."""

import pytest
from unittest.mock import AsyncMock

from app.alerts.ws_manager import AlertConnectionManager


@pytest.mark.asyncio
async def test_ws_manager_broadcast():
    manager = AlertConnectionManager()
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    manager._connections.append(mock_ws)

    await manager.broadcast("alert.created", {"alert_id": "test-123", "severity": "HIGH"})

    mock_ws.send_json.assert_called_once()
    payload = mock_ws.send_json.call_args[0][0]
    assert payload["event"] == "alert.created"
    assert payload["alert_id"] == "test-123"
