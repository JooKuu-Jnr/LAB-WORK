"""Entry point for Lab 4 simulation.

Starts a SensorAgent, CoordinatorAgent and two ResponseAgents.  Demonstrates the
FIPA-ACL workflow outlined in the lab instructions.

Run `python -m labs.lab4.main` from the project root after ensuring a local
XMPP server (e.g. `docker run --rm -p 5222:5222 rroemhildt/ejabberd`) is
available.
"""

import asyncio
import sys
from pathlib import Path

# ensure we can import packages from the project root
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from labs.lab4.agents.sensor_agent import SensorAgent  # noqa: E402
from labs.lab4.agents.coordinator_agent import CoordinatorAgent  # noqa: E402
from labs.lab4.agents.response_agent import ResponseAgent  # noqa: E402


async def main() -> None:
    print("=" * 60)
    print("Lab 4: Agent Communication (FIPA-ACL) Simulation")
    print("=" * 60)

    coord_jid = "coordinator@localhost"
    sensor_jid = "sensor_agent@localhost"
    responder_jids = ["responder1@localhost", "responder2@localhost"]

    # instantiate agents
    coordinator = CoordinatorAgent(
        jid=coord_jid,
        password="password",
        sensor_jid=sensor_jid,
        response_jids=responder_jids,
    )

    responders = [
        ResponseAgent(jid=r, password="password", coordinator_jid=coord_jid)
        for r in responder_jids
    ]

    sensor = SensorAgent(jid=sensor_jid, password="password", target_jid=coord_jid)

    # start all agents (allow them to register with the XMPP server if
    # the accounts do not already exist).  Connection failures are handled
    # gracefully so the script can explain the problem rather than crash.
    try:
        await coordinator.start(auto_register=True)
        print("Coordinator started.")

        for r in responders:
            await r.start(auto_register=True)
            print(f"Response agent {r.jid} started.")

        await sensor.start(auto_register=True)
        print("Sensor agent started.\n")
    except Exception as exc:  # usually spade.agent.DisconnectedException
        print("\n[Error] Unable to connect to XMPP server:", exc)
        print("Please ensure an XMPP server is running on localhost:5222 and"
              " that the hostname/domain in the JIDs matches the server config.")
        return

    try:
        while sensor.is_alive() and coordinator.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted, stopping all agents...")
    finally:
        if sensor.is_alive():
            await sensor.stop()
        for r in responders:
            if r.is_alive():
                await r.stop()
        if coordinator.is_alive():
            await coordinator.stop()
        print("All agents stopped. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())
