"""Tests for CoordinatorAgent behaviour by stubbing message reception and send."""

import sys, os
import asyncio
import pytest

# ensure project root importable
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from spade.message import Message

from labs.lab4.agents.coordinator_agent import CoordinatorAgent


class DummyHandler(CoordinatorAgent.MessageHandler):
    def __init__(self):
        super().__init__()
        self.sent_messages = []

    async def send(self, msg):
        # intercept outgoing messages for inspection
        self.sent_messages.append(msg)


@pytest.mark.asyncio
async def test_dispatch_requests():
    # set up a coordinator with two responders
    agent = CoordinatorAgent(
        jid="coord@localhost",
        password="password",
        sensor_jid="sensor@localhost",
        response_jids=["r1@localhost", "r2@localhost"],
    )
    beh = DummyHandler()
    beh.agent = agent

    # fabricate an INFORM from sensor
    msg = Message(to=agent.jid)
    msg.set_metadata("performative", "inform")
    msg.body = "GAS_LEAK_CONFIRMED"
    # message.sender is a JID object; use string for simplicity
    msg.sender = agent.sensor_jid

    async def fake_receive(timeout=None):
        return msg

    beh.receive = fake_receive

    await beh.run()

    # behaviour should have sent one request to each responder
    assert len(beh.sent_messages) == 2
    for m in beh.sent_messages:
        assert m.get_metadata("performative") == "request"
        assert "GAS_LEAK_CONFIRMED" in m.body


@pytest.mark.asyncio
async def test_handle_shutdown():
    agent = CoordinatorAgent(
        jid="coord@localhost",
        password="password",
        sensor_jid="sensor@localhost",
        response_jids=["r1@localhost"],
    )
    beh = DummyHandler()
    beh.agent = agent

    shutdown = Message(to=agent.jid)
    shutdown.set_metadata("performative", "inform")
    shutdown.body = "SHUTDOWN"
    shutdown.sender = agent.sensor_jid

    async def fake_receive(timeout=None):
        return shutdown

    beh.receive = fake_receive

    # once run executes, agent should be stopped (behaviour triggers stop)
    # we simulate by catching StopIteration as agent.stop() is a coroutine
    await beh.run()

    # expect that a shutdown inform was forwarded
    assert len(beh.sent_messages) == 1
    assert beh.sent_messages[0].body == "SHUTDOWN"
