"""Lab 2 – SPADE SensorAgent for LPG station perception.

This agent connects to the local XMPP server, periodically reads the
simulated LPG station environment, classifies hazard severity, generates
percept events, and writes structured log entries.

Hazard levels
-------------
    NORMAL   – gas concentration is within safe limits
    WARNING  – elevated readings; possible early leak
    DANGER   – confirmed gas leak
    CRITICAL – explosive-risk concentration

Event types
-----------
    NORMAL_CONDITION     – all readings within safe bounds
    POSSIBLE_GAS_LEAK    – early-warning threshold exceeded
    GAS_LEAK_CONFIRMED   – sustained dangerous concentration
    CRITICAL_GAS_LEVEL   – immediate evacuation required

Usage
-----
    python lab2_perception/agents/sensor_agent.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour

# ---------------------------------------------------------------------------
# Resolve paths so the script works when executed from the project root
# (i.e.  python lab2_perception/agents/sensor_agent.py)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent          # …/agents/
_LAB2_DIR = _SCRIPT_DIR.parent                         # …/lab2_perception/

# Allow imports from the lab2_perception package
sys.path.insert(0, str(_LAB2_DIR.parent))              # …/labs/

from lab2_perception.environment.simulated_lpg_station import SimulatedLPGStation  # noqa: E402

# ---------------------------------------------------------------------------
# Logging configuration – writes to  logs/events_lab2.log
# ---------------------------------------------------------------------------
_LOG_DIR = _LAB2_DIR / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "events_lab2.log"

logger = logging.getLogger("SensorAgent")
logger.setLevel(logging.INFO)

_file_handler = logging.FileHandler(_LOG_FILE, mode="a", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_file_handler)

# Also echo to stdout so the user can follow along
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_stream_handler)


# ── Perception thresholds ──────────────────────────────────────────────────
PPM_WARNING  = 200
PPM_DANGER   = 500
PPM_CRITICAL = 900


# ===========================================================================
# Hazard classification helpers
# ===========================================================================

def classify_hazard(lpg_ppm: float) -> str:
    """Return a hazard level string based on gas concentration (ppm).

    Thresholds are aligned with common industrial safety references:
        <200 ppm  → NORMAL
        200–499   → WARNING
        500–899   → DANGER
        ≥900      → CRITICAL
    """
    if lpg_ppm >= PPM_CRITICAL:
        return "CRITICAL"
    if lpg_ppm >= PPM_DANGER:
        return "DANGER"
    if lpg_ppm >= PPM_WARNING:
        return "WARNING"
    return "NORMAL"


def determine_event(hazard_level: str) -> str:
    """Map a hazard level to the corresponding percept event type."""
    mapping = {
        "NORMAL":   "NORMAL_CONDITION",
        "WARNING":  "POSSIBLE_GAS_LEAK",
        "DANGER":   "GAS_LEAK_CONFIRMED",
        "CRITICAL": "CRITICAL_GAS_LEVEL",
    }
    return mapping.get(hazard_level, "NORMAL_CONDITION")


# ===========================================================================
# SPADE Behaviour – periodic environment perception
# ===========================================================================

class PerceptionBehaviour(PeriodicBehaviour):
    """Reads the simulated environment every period and logs the percept.

    The behaviour:
        1. Calls ``get_current_readings()`` on the shared station model.
        2. Classifies the hazard level from gas concentration.
        3. Determines the percept event type.
        4. Writes a structured log line.
    """

    def __init__(self, period: float, station: SimulatedLPGStation) -> None:
        super().__init__(period=period)
        self.station = station
        self._cycles = 0
        self._max_cycles = 20  # stop after 20 readings for a clean demo

    async def run(self) -> None:
        """Execute one perception cycle."""
        readings = self.station.get_current_readings()

        lpg_ppm = readings["lpg_ppm"]
        pressure = readings["tank_pressure_kpa"]
        pump = readings["pump_state"]

        hazard = classify_hazard(lpg_ppm)
        event = determine_event(hazard)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_line = (
            f"{timestamp} | SensorAgent | "
            f"lpg_ppm={lpg_ppm} | pressure={pressure} | pump={pump} | "
            f"event={event} | hazard={hazard}"
        )
        logger.info(log_line)

        self._cycles += 1
        if self._cycles >= self._max_cycles:
            print("\n[SensorAgent] Demo complete – 20 perception cycles recorded.")
            await self.agent.stop()


# ===========================================================================
# SPADE Agent
# ===========================================================================

class SensorAgent(Agent):
    """SPADE agent that perceives the simulated LPG station environment.

    On setup the agent creates a ``SimulatedLPGStation`` instance and
    registers a ``PerceptionBehaviour`` that polls it every 2 seconds.
    """

    POLL_INTERVAL: float = 2.0  # seconds between readings

    async def setup(self) -> None:
        """Attach the periodic perception behaviour."""
        print(f"[SensorAgent] Setup complete for JID: {self.jid}")
        station = SimulatedLPGStation()
        behaviour = PerceptionBehaviour(
            period=self.POLL_INTERVAL,
            station=station,
        )
        self.add_behaviour(behaviour)


# ===========================================================================
# Entry point
# ===========================================================================

async def main() -> None:
    """Start the SensorAgent against the local XMPP server."""
    jid = "sensor_agent@localhost"
    password = "password"

    agent = SensorAgent(jid=jid, password=password)

    try:
        await asyncio.wait_for(agent.start(auto_register=True), timeout=15)
        print("[SensorAgent] Connected to localhost XMPP server. Monitoring started.\n")

        while agent.is_alive():
            await asyncio.sleep(0.5)

        print("[SensorAgent] Agent stopped successfully.")
    except asyncio.TimeoutError:
        print("[SensorAgent] Connection timed out. Is the XMPP server running?")
        if agent.is_alive():
            await agent.stop()
    except Exception as err:
        print(f"[SensorAgent] Startup failed: {err}")
        if agent.is_alive():
            await agent.stop()
    except KeyboardInterrupt:
        print("\n[SensorAgent] Interrupt received. Stopping…")
        if agent.is_alive():
            await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
