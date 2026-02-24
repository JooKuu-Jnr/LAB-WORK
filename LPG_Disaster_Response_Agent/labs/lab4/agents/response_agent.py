"""Generic response agent for Lab 4.

Listens for REQUEST messages from the CoordinatorAgent. When a request arrives the
agent simulates performing an action then sends an INFORM back to the
coordinator confirming completion.  A special SHUTDOWN inform stops the agent.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

# path hack so we can import other labs if necessary
_SCRIPT_DIR = Path(__file__).resolve().parent
_LAB4_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_LAB4_DIR.parent))


class ResponseAgent(Agent):
    def __init__(self, jid: str, password: str, coordinator_jid: str, *args, **kwargs):
        super().__init__(jid, password, *args, **kwargs)
        self.coordinator_jid = coordinator_jid

    class HandleRequests(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=3)
            if msg:
                perf = msg.get_metadata("performative")
                body = msg.body
                sender = str(msg.sender)

                if perf == "request":
                    print(f"[{self.agent.jid}] received REQUEST {body} from {sender}")
                    # simulate a bit of work
                    await asyncio.sleep(1)
                    reply = Message(to=self.agent.coordinator_jid)
                    reply.set_metadata("performative", "inform")
                    reply.body = f"completed_{body}"
                    await self.send(reply)
                    print(f"[{self.agent.jid}] sent INFORM back: {reply.body}")
                elif body == "SHUTDOWN":
                    print(f"[{self.agent.jid}] shutdown signal received, stopping agent.")
                    await self.agent.stop()
            else:
                await asyncio.sleep(0.2)

    async def setup(self) -> None:
        print(f"[ResponseAgent] setup complete for {self.jid}")
        self.add_behaviour(self.HandleRequests())


async def main() -> None:
    # Example executor for a single responder
    agent = ResponseAgent(
        jid="responder1@localhost",
        password="password",
        coordinator_jid="coordinator@localhost",
    )
    try:
        await agent.start(auto_register=True)
        print(f"[{agent.jid}] running")
        while agent.is_alive():
            await asyncio.sleep(0.5)
    finally:
        if agent.is_alive():
            await agent.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
