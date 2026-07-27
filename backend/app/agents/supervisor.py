from dataclasses import dataclass
from typing import Sequence

from .recommendation import RecommendationAgent
from .risk_evaluation import RiskEvaluationAgent
from .trend_detection import TrendDetectionAgent
from .vital_analysis import VitalAnalysisAgent


@dataclass
class SupervisorAgent:
    vital_agent: VitalAnalysisAgent
    trend_agent: TrendDetectionAgent
    risk_agent: RiskEvaluationAgent
    recommendation_agent: RecommendationAgent

    def run(self, profile: object, samples: Sequence[object]) -> dict:
        vital_analysis = self.vital_agent.run(samples)
        trend_analysis = self.trend_agent.run(samples)
        risk_evaluation = self.risk_agent.run(samples, vital_analysis, trend_analysis)
        recommendation = self.recommendation_agent.run(samples, vital_analysis, trend_analysis, risk_evaluation)

        return {
            "profile": profile,
            "latest": samples[-1],
            "vital_analysis": vital_analysis,
            "trend_analysis": trend_analysis,
            "risk_evaluation": risk_evaluation,
            "recommendation": recommendation,
        }
