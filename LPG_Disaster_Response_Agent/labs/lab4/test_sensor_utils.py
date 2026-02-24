"""Unit tests for sensor classification utilities."""

import sys, os

# make sure project root is on sys.path so that `labs` package can be imported
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root not in sys.path:
    sys.path.insert(0, root)

import pytest

from labs.lab4.agents.sensor_agent import classify_hazard, determine_event


@pytest.mark.parametrize(
    "ppm,expected",
    [
        (0, "NORMAL"),
        (200, "WARNING"),
        (499.9, "WARNING"),
        (500, "DANGER"),
        (899.9, "DANGER"),
        (900, "CRITICAL"),
        (1500, "CRITICAL"),
    ],
)
def test_classify_hazard(ppm, expected):
    assert classify_hazard(ppm) == expected


@pytest.mark.parametrize(
    "level,expected_event",
    [
        ("NORMAL", "NORMAL_CONDITION"),
        ("WARNING", "POSSIBLE_GAS_LEAK"),
        ("DANGER", "GAS_LEAK_CONFIRMED"),
        ("CRITICAL", "CRITICAL_GAS_LEVEL"),
        ("UNKNOWN", "NORMAL_CONDITION"),
    ],
)
def test_determine_event(level, expected_event):
    assert determine_event(level) == expected_event
