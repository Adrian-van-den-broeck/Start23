"""HTTP contract tests for the narrow Polar AccessLink adapter."""

import asyncio
import base64
from urllib.parse import parse_qs, urlparse

import httpx

from app.core.config import Settings
from app.modules.integrations.polar import PolarAccessLinkClient


def _settings() -> Settings:
    return Settings(
        environment="test",
        polar_client_id="polar-client",
        polar_client_secret="polar-secret",
        polar_webhook_secret="webhook-secret",
        polar_oauth_redirect_url=(
            "https://api.start23.example/api/v1/integrations/polar/oauth/callback"
        ),
    )


def test_authorization_url_has_state_scope_and_exact_redirect() -> None:
    provider = PolarAccessLinkClient(_settings())
    parsed = urlparse(provider.authorization_url("one-time-state"))
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.hostname == "flow.polar.com"
    assert query == {
        "response_type": ["code"],
        "client_id": ["polar-client"],
        "redirect_uri": [
            "https://api.start23.example/api/v1/integrations/polar/oauth/callback"
        ],
        "scope": ["accesslink.read_all"],
        "state": ["one-time-state"],
    }
    assert "polar-secret" not in provider.authorization_url("one-time-state")
    asyncio.run(provider.aclose())


def test_token_exchange_and_revocation_follow_provider_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "polarremote.com":
            return httpx.Response(
                200,
                json={
                    "access_token": "provider-access-token-value",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "x_user_id": 475,
                },
            )
        return httpx.Response(204)

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = PolarAccessLinkClient(_settings(), client=client)
            token = await provider.exchange_code("one-time-code")
            assert token.provider_user_id == "475"
            await provider.revoke(token.access_token, token.provider_user_id)

    asyncio.run(exercise())

    expected_basic = base64.b64encode(b"polar-client:polar-secret").decode()
    assert requests[0].headers["authorization"] == f"Basic {expected_basic}"
    assert requests[0].url.path == "/v2/oauth2/token"
    assert b"grant_type=authorization_code" in requests[0].content
    assert requests[1].method == "DELETE"
    assert requests[1].url.path == "/v3/users/475"
    assert requests[1].headers["authorization"] == "Bearer provider-access-token-value"
