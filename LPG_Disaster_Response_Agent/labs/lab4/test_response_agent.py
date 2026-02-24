"""Unit tests for ResponseAgent handling of requests."""

import sys, os
import pytest
from spade.message import Message

# add project root to path so the labs package is found
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from labs.lab4.agents.response_agent import ResponseAgent


class DummyRespBehaviour(ResponseAgent.HandleRequests):
    def __init__(self):
        super().__init__()
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


@pytest.mark.asyncio
async def test_process_request():
    agent = ResponseAgent(
        jid="r@localhost",
        password="pass",
        coordinator_jid="coord@localhost",
    )
    beh = DummyRespBehaviour()
    beh.agent = agent

    msg = Message()
    msg.set_metadata("performative", "request")
    msg.body = "handle_GAS_LEAK_CONFIRMED"
    msg.sender = "sensor@localhost"

    async def fake_receive(timeout=None):
        return msg

    beh.receive = fake_receive

    await beh.run()

    assert len(beh.sent) == 1
    out = beh.sent[0]
    assert out.get_metadata("performative") == "inform"
    assert "completed_" in out.body


@pytest.mark.asyncio
async def test_shutdown_message():
    agent = ResponseAgent(
        jid="r@localhost",
        password="pass",
        coordinator_jid="coord@localhost",
    )
    beh = DummyRespBehaviour()
    beh.agent = agent

    msg = Message()
    msg.set_metadata("performative", "inform")
    msg.body = "SHUTDOWN"
    msg.sender = "coord@localhost"

    async def fake_receive(timeout=None):
        return msg

    beh.receive = fake_receive

    # run should stop the agent
    await beh.run()
    assert beh.agent.is_alive() is False
