from typing import Sequence

from .base import Agent


class RecommendationAgent(Agent):
    def run(
        self,
        samples: Sequence[object],
        vital_analysis: dict,
        trend_analysis: dict,
        risk_evaluation: dict,
    ) -> dict:
        latest = samples[-1]
        current_condition = risk_evaluation["current_condition"]
        label = risk_evaluation["label"]

        prediction_map = {
            "Normal": "Patient remains physiologically stable with no dominant abnormal pattern.",
            "Hypoxia": "Respiratory instability is active and oxygenation support should be reviewed.",
            "Fever": "Persistent temperature elevation suggests an inflammatory or infectious burden.",
            "Cardiac Stress": "Cardiac workload remains elevated and rhythm needs close attention.",
            "Sepsis Risk": "Combined fever, tachycardia, and low SpO2 suggest possible sepsis escalation.",
            "Recovery": "The patient shows signs of physiological recovery with improving trends.",
        }

        action_map = {
            "Normal": "Continue routine monitoring and preserve the current baseline for comparison.",
            "Hypoxia": "Check airway, oxygen delivery, and respiratory support settings.",
            "Fever": "Review infection markers and reinforce fever management.",
            "Cardiac Stress": "Escalate cardiac review and monitor rhythm and workload closely.",
            "Sepsis Risk": "Escalate now and assess circulation, cultures, antibiotics, and organ support.",
            "Recovery": "Continue observation and confirm that improvement is sustained.",
        }

        reasons = []
        alerts = []

        if latest.spo2 < 94:
            reasons.append(f"SpO2 is {latest.spo2:.1f}%, below the preferred threshold of 95%.")
        elif trend_analysis["spo2_slope"] < -1.0:
            reasons.append(f"SpO2 has fallen by {abs(trend_analysis['spo2_slope']):.1f} points in the active trend window.")
        else:
            reasons.append(f"Average SpO2 is {trend_analysis['spo2_average']:.1f}%, which is currently acceptable.")

        if latest.heart_rate > 105 or latest.heart_rate < 56:
            reasons.append(f"Heart rate is {latest.heart_rate:.0f} bpm, outside the preferred ICU band.")
        elif abs(trend_analysis["heart_slope"]) > 10:
            reasons.append("Heart rate changed rapidly across the recent monitoring window.")
        else:
            reasons.append(f"Average heart rate is {trend_analysis['heart_average']:.0f} bpm.")

        if latest.temperature >= 38.0:
            reasons.append(f"Temperature is {latest.temperature:.1f} C and supports a fever or inflammatory signal.")
        elif trend_analysis["temp_slope"] > 0.25:
            reasons.append("Temperature is trending upward and needs closer observation.")
        else:
            reasons.append(f"Average temperature is {trend_analysis['temp_average']:.1f} C.")

        if latest.spo2 < 90:
            alerts.append("Critical drop in SpO2 detected.")
        if latest.heart_rate > 120:
            alerts.append("Heart rate spike detected above the safe range.")
        if latest.temperature >= 39.0:
            alerts.append("Temperature spike suggests worsening systemic stress.")
        if label == "Critical" and not alerts:
            alerts.append("AI agents detected a critical deterioration pattern.")

        return {
            "prediction": prediction_map[current_condition],
            "action": action_map[current_condition],
            "reasons": reasons[:3],
            "alerts": alerts,
        }
