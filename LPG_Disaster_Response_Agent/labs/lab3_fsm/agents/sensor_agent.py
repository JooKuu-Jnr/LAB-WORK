"""Lab 3 – SPADE SensorAgent for generating percepts and sending FSM events.

This agent connects to the local XMPP server, periodically reads the
simulated LPG station environment, classifies hazard severity, generates
percept events, and sends them via XMPP messages to the FSM Agent.
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

# Resolve paths
_SCRIPT_DIR = Path(__file__).resolve().parent
_LAB3_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_LAB3_DIR.parent))

from lab2_perception.environment.simulated_lpg_station import SimulatedLPGStation  # noqa: E402

logger = logging.getLogger("SensorAgent")
logger.setLevel(logging.INFO)
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_stream_handler)

PPM_WARNING  = 200
PPM_DANGER   = 500
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
        "NORMAL":   "NORMAL_CONDITION",
        "WARNING":  "POSSIBLE_GAS_LEAK",
        "DANGER":   "GAS_LEAK_CONFIRMED",
        "CRITICAL": "CRITICAL_GAS_LEVEL",
    }
    return mapping.get(hazard_level, "NORMAL_CONDITION")

class PerceptionBehaviour(PeriodicBehaviour):
    def __init__(self, period: float, station: SimulatedLPGStation, target_jid: str) -> None:
        super().__init__(period=period)
        self.station = station
        self.target_jid = target_jid
        self._cycles = 0
        self._max_cycles = 25  # enough cycles to see all transitions

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

        # Send event to the FSM agent
        msg = Message(to=self.target_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "lpg_station_ontology")
        msg.body = event
        
        await self.send(msg)

        self._cycles += 1
        if self._cycles >= self._max_cycles:
            logger.info("\n[SensorAgent] Simulation complete – sending shutdown signal.")
            # Send a specific completion signal to shut down the FSM cleanly if needed, though testing it simply is fine.
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
        logger.info(f"[SensorAgent] Setup complete for JID: {self.jid}")
        station = SimulatedLPGStation(normal_duration=4, leak_duration=10) # Faster cycling for testing
        behaviour = PerceptionBehaviour(
            period=self.POLL_INTERVAL,
            station=station,
            target_jid=self.target_jid
        )
        self.add_behaviour(behaviour)

async def main() -> None:
    jid = "sensor_agent@localhost"
    password = "password"
    target_jid = "fsm_agent@localhost"

    agent = SensorAgent(jid=jid, password=password, target_jid=target_jid)

    try:
        await asyncio.wait_for(agent.start(auto_register=True), timeout=15)
        logger.info("[SensorAgent] Connected to localhost XMPP server. Monitoring started.\n")

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
