from typing import Sequence

from .base import Agent


class RiskEvaluationAgent(Agent):
    def run(self, samples: Sequence[object], vital_analysis: dict, trend_analysis: dict) -> dict:
        latest = samples[-1]
        score = 8

        if latest.spo2 < 90:
            score += 38
        elif latest.spo2 < 94:
            score += 24
        elif trend_analysis["spo2_slope"] < -1.0:
            score += 10

        if latest.heart_rate > 120 or latest.heart_rate < 50:
            score += 28
        elif latest.heart_rate > 105 or latest.heart_rate < 56:
            score += 16
        elif abs(trend_analysis["heart_slope"]) > 10:
            score += 8

        if latest.temperature >= 39.0:
            score += 26
        elif latest.temperature >= 38.0:
            score += 14
        elif trend_analysis["temp_slope"] > 0.25:
            score += 6

        if trend_analysis["improving"]:
            score -= 14

        score = max(5, min(98, round(score)))

        if score >= 70:
            label = "Critical"
        elif score >= 38:
            label = "Moderate"
        else:
            label = "Stable"

        if latest.temperature >= 38.8 and latest.heart_rate > 110 and latest.spo2 < 94:
            current_condition = "Sepsis Risk"
        elif latest.spo2 < 94:
            current_condition = "Hypoxia"
        elif latest.temperature >= 38.0:
            current_condition = "Fever"
        elif latest.heart_rate > 110:
            current_condition = "Cardiac Stress"
        elif trend_analysis["improving"] and latest.spo2 > 95 and latest.temperature < 37.5:
            current_condition = "Recovery"
        else:
            current_condition = "Normal"

        if label == "Critical":
            tone = "critical"
            danger_text = "Immediate bedside attention is recommended."
        elif label == "Moderate":
            tone = "moderate"
            danger_text = "There is measurable risk and this patient needs closer observation."
        else:
            tone = "stable"
            danger_text = "No immediate danger is detected in the current window."

        return {
            "label": label,
            "score": score,
            "tone": tone,
            "current_condition": current_condition,
            "danger_text": danger_text,
        }
