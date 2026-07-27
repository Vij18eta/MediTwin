from typing import Sequence

from .base import Agent


def status_from_ranges(value: float, normal_low: float, normal_high: float, critical_low: float, critical_high: float) -> str:
    if value <= critical_low or value >= critical_high:
        return "critical"
    if value < normal_low or value > normal_high:
        return "moderate"
    return "stable"


class VitalAnalysisAgent(Agent):
    def run(self, samples: Sequence[object]) -> dict:
        latest = samples[-1]

        heart_status = status_from_ranges(latest.heart_rate, 60, 100, 50, 120)
        spo2_status = status_from_ranges(latest.spo2, 95, 100, 90, 101)
        temperature_status = status_from_ranges(latest.temperature, 36.5, 37.5, 35.9, 39.0)

        flags = []
        if spo2_status != "stable":
            flags.append(f"SpO2 is {latest.spo2:.1f}%")
        if heart_status != "stable":
            flags.append(f"Heart rate is {latest.heart_rate:.0f} bpm")
        if temperature_status != "stable":
            flags.append(f"Temperature is {latest.temperature:.1f} C")

        return {
            "latest": latest,
            "heart_status": heart_status,
            "spo2_status": spo2_status,
            "temperature_status": temperature_status,
            "flags": flags,
        }
