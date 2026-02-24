from __future__ import annotations

import asyncio

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour


class StartupBehaviour(OneShotBehaviour):
    """A one-time behaviour used to confirm that the agent is active."""

    async def run(self) -> None:
        """Execute a minimal task and stop the agent cleanly."""
        print("[BasicAgent] Behaviour executing: system heartbeat check complete.")
        await asyncio.sleep(1)
        print("[BasicAgent] Behaviour finished. Initiating clean shutdown.")
        await self.agent.stop()


class BasicAgent(Agent):
    """Minimal SPADE agent for Lab 1 environment validation."""

    async def setup(self) -> None:
        """Register startup behaviour after successful connection."""
        print(f"[BasicAgent] Agent setup complete for JID: {self.jid}")
        self.add_behaviour(StartupBehaviour())


async def main() -> None:
    """Start the agent, wait for completion, and handle shutdown safely."""
    jid = "test_agent@localhost"
    password = "password"

    agent = BasicAgent(jid=jid, password=password)

    try:
        await asyncio.wait_for(agent.start(auto_register=False), timeout=10)
        print("[BasicAgent] Agent is running and connected to localhost XMPP server.")

        while agent.is_alive():
            await asyncio.sleep(0.5)

        print("[BasicAgent] Agent stopped successfully.")
    except asyncio.TimeoutError:
        print("[BasicAgent] Connection timed out. Verify that the localhost XMPP server is running.")
        if agent.is_alive():
            await agent.stop()
    except Exception as error:
        print(f"[BasicAgent] Startup failed: {error}")
        if agent.is_alive():
            await agent.stop()
    except KeyboardInterrupt:
        print("\n[BasicAgent] Interrupt received. Stopping agent...")
        if agent.is_alive():
            await agent.stop()
        print("[BasicAgent] Agent stopped after interrupt.")


if __name__ == "__main__":
    asyncio.run(main())
