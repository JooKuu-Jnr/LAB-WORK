"""Coordinator agent for Lab 4.

Receives INFORM messages from the SensorAgent and issues REQUESTs to one or more
ResponseAgents.  ResponseAgents send INFORMs back when they complete the task.

This simple workflow demonstrates FIPA-ACL performatives and multi-agent
coordination.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

# path hack so we can import other labs
_SCRIPT_DIR = Path(__file__).resolve().parent
_LAB4_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_LAB4_DIR.parent))


class CoordinatorAgent(Agent):
    def __init__(
        self,
        jid: str,
        password: str,
        sensor_jid: str,
        response_jids: list[str],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(jid, password, *args, **kwargs)
        self.sensor_jid = sensor_jid
        self.response_jids = response_jids

    class MessageHandler(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=3)
            if msg:
                body = msg.body
                perf = msg.get_metadata("performative")
                sender = str(msg.sender)

                # shutdown signal from sensor
                if body == "SHUTDOWN":
                    print("[Coordinator] received shutdown request. Forwarding to responses and stopping.")
                    for r in self.agent.response_jids:
                        shutdown_msg = Message(to=r)
                        shutdown_msg.set_metadata("performative", "inform")
                        shutdown_msg.body = "SHUTDOWN"
                        await self.send(shutdown_msg)
                    await self.agent.stop()
                    return

                # message from sensor
                if sender.startswith(self.agent.sensor_jid):
                    print(f"[Coordinator] INFORM from sensor -> event={body}")
                    # dispatch REQUESTs to responders
                    for r in self.agent.response_jids:
                        request = Message(to=r)
                        request.set_metadata("performative", "request")
                        request.set_metadata("ontology", "lpg_station_ontology")
                        request.body = f"handle_{body}"
                        await self.send(request)
                        print(f"[Coordinator] sent REQUEST to {r}: {request.body}")
                else:
                    # assume feedback from a response agent
                    print(f"[Coordinator] received {perf.upper()} from {sender}: {body}")
            else:
                await asyncio.sleep(0.2)

    async def setup(self) -> None:
        print(f"[Coordinator] setup complete for {self.jid}")
        self.add_behaviour(self.MessageHandler())


async def main() -> None:
    # quick standalone runner for experimentation
    coord = CoordinatorAgent(
        jid="coordinator@localhost",
        password="password",
        sensor_jid="sensor_agent@localhost",
        response_jids=["responder1@localhost", "responder2@localhost"],
    )
    try:
        await coord.start(auto_register=True)
        print("[Coordinator] agent running")
        while coord.is_alive():
            await asyncio.sleep(0.5)
    finally:
        if coord.is_alive():
            await coord.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
