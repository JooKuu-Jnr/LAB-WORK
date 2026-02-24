"""Simulated LPG filling-station environment for Lab 2.

This module models the physical environment that the SensorAgent perceives.
Three percept variables are simulated:

    lpg_ppm           – parts-per-million of LPG gas in the air
    tank_pressure_kpa – pressure inside the storage tank (kPa)
    pump_state        – whether the dispensing pump is ON or OFF

The simulation alternates between a **normal** operating window and a
**leak** scenario so that the SensorAgent can exercise all hazard levels.
"""

from __future__ import annotations

import random
import time


class SimulatedLPGStation:
    """Generates realistic, time-varying LPG station sensor readings.

    The station cycles through two phases:
        1. Normal operation  – low gas concentration, stable pressure.
        2. Leak scenario     – gas concentration rises gradually and
                               tank pressure drops, simulating a leak.

    Parameters
    ----------
    normal_duration : int
        Approximate number of readings before a leak begins (default 10).
    leak_duration : int
        Approximate number of readings the leak persists (default 8).
    """

    # ── Realistic operating ranges ──────────────────────────────────────
    NORMAL_PPM_RANGE = (0, 200)           # safe ambient LPG concentration
    WARNING_PPM_RANGE = (200, 500)        # early-warning zone
    DANGER_PPM_RANGE = (500, 900)         # confirmed leak territory
    CRITICAL_PPM_THRESHOLD = 900          # explosive-risk threshold

    NORMAL_PRESSURE_RANGE = (800, 1200)   # healthy tank pressure (kPa)
    LEAK_PRESSURE_DROP = (5, 25)          # pressure lost per tick in a leak

    def __init__(
        self,
        normal_duration: int = 10,
        leak_duration: int = 8,
    ) -> None:
        self.normal_duration = normal_duration
        self.leak_duration = leak_duration

        # Internal state
        self._tick = 0
        self._phase: str = "normal"       # "normal" | "leak"
        self._phase_start: int = 0
        self._lpg_ppm: float = 50.0
        self._tank_pressure: float = random.uniform(950, 1100)
        self._pump_on: bool = True

    # ── Public API ──────────────────────────────────────────────────────

    def get_current_readings(self) -> dict:
        """Return the latest simulated sensor readings as a dictionary.

        Returns
        -------
        dict
            Keys: ``lpg_ppm``, ``tank_pressure_kpa``, ``pump_state``.
        """
        self._advance()
        return {
            "lpg_ppm": round(self._lpg_ppm, 1),
            "tank_pressure_kpa": round(self._tank_pressure, 1),
            "pump_state": "ON" if self._pump_on else "OFF",
        }

    # ── Internal simulation logic ───────────────────────────────────────

    def _advance(self) -> None:
        """Move the simulation forward by one tick and update readings."""
        self._tick += 1
        elapsed = self._tick - self._phase_start

        if self._phase == "normal":
            self._simulate_normal()
            # Transition to leak after the normal window elapses
            if elapsed >= self.normal_duration:
                self._phase = "leak"
                self._phase_start = self._tick
        else:
            self._simulate_leak(elapsed)
            # Transition back to normal after the leak window elapses
            if elapsed >= self.leak_duration:
                self._reset_to_normal()

    def _simulate_normal(self) -> None:
        """Generate readings within safe operating bounds."""
        self._lpg_ppm = random.uniform(*self.NORMAL_PPM_RANGE)
        # Pressure stays stable with small fluctuations
        self._tank_pressure += random.uniform(-5, 5)
        self._tank_pressure = max(800, min(1200, self._tank_pressure))
        # Pump toggles occasionally
        self._pump_on = random.random() > 0.2

    def _simulate_leak(self, elapsed: int) -> None:
        """Gradually worsen readings to simulate a developing gas leak.

        The gas concentration rises linearly with each tick so the agent
        traverses WARNING → DANGER → CRITICAL levels over time.
        """
        # Gas concentration climbs as the leak progresses
        base = self.NORMAL_PPM_RANGE[1]
        self._lpg_ppm = base + elapsed * random.uniform(80, 120)
        self._lpg_ppm = min(self._lpg_ppm, 1500)  # cap at realistic max

        # Tank pressure drops steadily
        self._tank_pressure -= random.uniform(*self.LEAK_PRESSURE_DROP)
        self._tank_pressure = max(400, self._tank_pressure)

        # Pump is forced ON during a leak (fuel still flowing)
        self._pump_on = True

    def _reset_to_normal(self) -> None:
        """Return the station to safe operating conditions."""
        self._phase = "normal"
        self._phase_start = self._tick
        self._lpg_ppm = random.uniform(30, 100)
        self._tank_pressure = random.uniform(950, 1100)
        self._pump_on = True
