from statistics import mean
from typing import Sequence

from .base import Agent


def compute_slope(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return values[-1] - values[0]


class TrendDetectionAgent(Agent):
    def run(self, samples: Sequence[object]) -> dict:
        recent = list(samples)[-8:]
        spo2_values = [sample.spo2 for sample in recent]
        heart_values = [sample.heart_rate for sample in recent]
        temp_values = [sample.temperature for sample in recent]

        spo2_slope = compute_slope(spo2_values)
        heart_slope = compute_slope(heart_values)
        temp_slope = compute_slope(temp_values)

        improving = (
            spo2_slope > 0.6
            and heart_slope < -4
            and temp_slope < -0.15
            and recent[-1].temperature < 37.5
        )

        worsening = (
            spo2_slope < -1.0
            or heart_slope > 9
            or temp_slope > 0.25
        )

        return {
            "spo2_slope": spo2_slope,
            "heart_slope": heart_slope,
            "temp_slope": temp_slope,
            "spo2_average": mean(spo2_values),
            "heart_average": mean(heart_values),
            "temp_average": mean(temp_values),
            "improving": improving,
            "worsening": worsening,
        }
