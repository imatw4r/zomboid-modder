from dataclasses import dataclass

import pytest

from zomboid_modder.core.bus import MessageBus


@dataclass(frozen=True)
class Ping:
    pass


@dataclass(frozen=True)
class Pong:
    n: int


async def test_send_routes_to_registered_handler():
    bus = MessageBus()
    seen = []

    async def handler(cmd):
        seen.append(cmd)

    bus.register(Ping, handler)
    await bus.send(Ping())
    assert seen == [Ping()]


async def test_send_raises_without_handler():
    bus = MessageBus()
    with pytest.raises(RuntimeError):
        await bus.send(Ping())


async def test_double_register_raises():
    bus = MessageBus()

    async def h(_):
        return None

    bus.register(Ping, h)
    with pytest.raises(RuntimeError):
        bus.register(Ping, h)


async def test_publish_fans_to_listeners():
    bus = MessageBus()
    a, b = [], []

    async def la(e):
        a.append(e)

    async def lb(e):
        b.append(e)

    bus.subscribe(Pong, la)
    bus.subscribe(Pong, lb)
    await bus.publish(Pong(1))
    assert a == [Pong(1)]
    assert b == [Pong(1)]


async def test_unsubscribe_removes_listener():
    bus = MessageBus()
    calls = []

    async def l(e):
        calls.append(e)

    unsub = bus.subscribe(Pong, l)
    await bus.publish(Pong(1))
    unsub()
    await bus.publish(Pong(2))
    assert calls == [Pong(1)]


async def test_listener_exception_does_not_stop_others():
    bus = MessageBus()
    calls = []

    async def bad(_):
        raise RuntimeError("boom")

    async def good(e):
        calls.append(e)

    bus.subscribe(Pong, bad)
    bus.subscribe(Pong, good)
    await bus.publish(Pong(1))
    assert calls == [Pong(1)]
