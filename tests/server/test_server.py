from everything import server
from mead import context, response
from mead.objects import JSONObject
import pytest
from unittest.mock import Mock


@pytest.fixture
def loop():
    import asyncio
    return asyncio.get_event_loop()

def awaitable(obj):
    async def justreturn():
        return obj

    return justreturn()


def test_auth_with_no_session(loop):
    async def go():
        ctx = context.Context(params=awaitable(Mock()), query=awaitable(Mock()), session=awaitable({"user": ""}))
        expect = response(JSONObject({
            "results": {
                "message": "You are not authorized."
            }
        }))
        result = await server.auth(ctx)
        assert result.body == expect.body


    loop.run_until_complete(go())


def test_auth_with_session(loop):
    async def go():
        ctx = context.Context(params=awaitable(Mock()), query=awaitable(Mock()), session=awaitable({"user": "John"}))
        expect = response(JSONObject({
            "results": {
                "auth": {
                    "name": "John"
                }
            }
        }))
        result = await server.auth(ctx)
        assert result.body == expect.body


    loop.run_until_complete(go())
