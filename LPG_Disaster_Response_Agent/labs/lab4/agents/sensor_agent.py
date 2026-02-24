"""Lab 4 – SensorAgent that notifies a CoordinatorAgent via FIPA-ACL INFORM.

The agent polls the same simulated LPG station used in earlier labs, classifies
hazard levels and then sends an INFORM message to a coordinator whenever the
reading is not NORMAL.  A special ``SHUTDOWN`` inform is emitted at the end of
the simulation so that the coordinator and response agents can terminate
cleanly.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message

# adjust path so we can import lab2 environment package
_SCRIPT_DIR = Path(__file__).resolve().parent
_LAB4_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_LAB4_DIR.parent))

from lab2_perception.environment.simulated_lpg_station import SimulatedLPGStation  # noqa: E402

logger = logging.getLogger("Lab4.SensorAgent")
logger.setLevel(logging.INFO)
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_stream_handler)

PPM_WARNING = 200
PPM_DANGER = 500
PPM_CRITICAL = 900


def classify_hazard(lpg_ppm: float) -> str:
    if lpg_ppm >= PPM_CRITICAL:
        return "CRITICAL"
    if lpg_ppm >= PPM_DANGER:
        return "DANGER"
    if lpg_ppm >= PPM_WARNING:
        return "WARNING"
    return "NORMAL"


def determine_event(hazard_level: str) -> str:
    mapping = {
        "NORMAL": "NORMAL_CONDITION",
        "WARNING": "POSSIBLE_GAS_LEAK",
        "DANGER": "GAS_LEAK_CONFIRMED",
        "CRITICAL": "CRITICAL_GAS_LEVEL",
    }
    return mapping.get(hazard_level, "NORMAL_CONDITION")


class PerceptionBehaviour(PeriodicBehaviour):
    def __init__(self, period: float, station: SimulatedLPGStation, target_jid: str) -> None:
        super().__init__(period=period)
        self.station = station
        self.target_jid = target_jid
        self._cycles = 0
        self._max_cycles = 25  # run long enough to exercise all hazard stages

    async def run(self) -> None:
        readings = self.station.get_current_readings()
        lpg_ppm = readings["lpg_ppm"]
        pressure = readings["tank_pressure_kpa"]
        pump = readings["pump_state"]

        hazard = classify_hazard(lpg_ppm)
        event = determine_event(hazard)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_line = (
            f"{timestamp} | SensorAgent | "
            f"lpg_{lpg_ppm}ppm | pres_{pressure}kPa | pump_{pump} | "
            f"event={event}"
        )
        logger.info(log_line)

        # send FIPA-ACL INFORM to coordinator
        msg = Message(to=self.target_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "lpg_station_ontology")
        msg.body = event
        await self.send(msg)

        self._cycles += 1
        if self._cycles >= self._max_cycles:
            logger.info("\n[SensorAgent] Simulation complete – sending SHUTDOWN inform.")
            shutdown_msg = Message(to=self.target_jid)
            shutdown_msg.set_metadata("performative", "inform")
            shutdown_msg.body = "SHUTDOWN"
            await self.send(shutdown_msg)
            await self.agent.stop()


class SensorAgent(Agent):
    POLL_INTERVAL: float = 2.0

    def __init__(self, jid: str, password: str, target_jid: str, *args, **kwargs):
        super().__init__(jid, password, *args, **kwargs)
        self.target_jid = target_jid

    async def setup(self) -> None:
        logger.info(f"[SensorAgent] setup complete for JID: {self.jid}")
        station = SimulatedLPGStation(normal_duration=4, leak_duration=10)
        behaviour = PerceptionBehaviour(
            period=self.POLL_INTERVAL,
            station=station,
            target_jid=self.target_jid,
        )
        self.add_behaviour(behaviour)


async def main() -> None:
    # Example stand‑alone execution (useful for debugging)
    jid = "sensor_agent@localhost"
    password = "password"
    coord_jid = "coordinator@localhost"

    agent = SensorAgent(jid=jid, password=password, target_jid=coord_jid)
    try:
        await asyncio.wait_for(agent.start(auto_register=True), timeout=15)
        logger.info("[SensorAgent] Connected to XMPP server. Monitoring started.\n")
        while agent.is_alive():
            await asyncio.sleep(0.5)
        logger.info("[SensorAgent] Agent stopped successfully.")
    except Exception as err:
        logger.error(f"[SensorAgent] Error: {err}")
        if agent.is_alive():
            await agent.stop()
    except KeyboardInterrupt:
        logger.info("\n[SensorAgent] Interrupt received. Stopping…")
        if agent.is_alive():
            await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
