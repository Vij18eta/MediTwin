from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import random


@dataclass
class VitalSample:
    time: datetime
    spo2: float
    heart_rate: float
    temperature: float


def clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def seeded_series(profile: object, total_points: int = 20) -> list[VitalSample]:
    points: list[VitalSample] = []
    now = now_utc()

    for index in range(total_points - 1, -1, -1):
        phase = (total_points - index) / 3
        progress = (total_points - index) / total_points

        if profile.simulation_pattern == "normal":
            spo2 = 98.1 + math.sin(phase) * 0.35
            heart_rate = 75 + math.cos(phase * 0.9) * 4.2
            temperature = 36.9 + math.sin(phase * 0.6) * 0.08
        elif profile.simulation_pattern == "hypoxia":
            spo2 = 92.2 + math.sin(phase * 1.2) * 0.9 - progress * 0.2
            heart_rate = 97 + math.cos(phase) * 4.5
            temperature = 37.1 + math.sin(phase * 0.7) * 0.05
        elif profile.simulation_pattern == "fever":
            spo2 = 96.8 + math.sin(phase * 0.8) * 0.4
            heart_rate = 92 + math.cos(phase * 0.7) * 5
            temperature = 38.4 + math.sin(phase) * 0.15 + progress * 0.08
        elif profile.simulation_pattern == "cardiac":
            spo2 = 96.1 + math.sin(phase * 0.8) * 0.4
            heart_rate = 117 + math.cos(phase * 1.1) * 7.5
            temperature = 37.2 + math.sin(phase * 0.5) * 0.08
        elif profile.simulation_pattern == "sepsis":
            spo2 = 92.5 + math.sin(phase) * 0.8 - progress * 0.35
            heart_rate = 121 + math.cos(phase * 0.9) * 6 + progress * 3.5
            temperature = 39.0 + math.sin(phase * 0.9) * 0.18 + progress * 0.14
        else:
            spo2 = 94.0 + progress * 3 + math.sin(phase) * 0.4
            heart_rate = 98 - progress * 16 + math.cos(phase * 0.8) * 4.5
            temperature = 37.8 - progress * 0.7 + math.sin(phase * 0.6) * 0.08

        points.append(
            VitalSample(
                time=now - timedelta(minutes=index * 3),
                spo2=clamp(spo2, 84, 100),
                heart_rate=clamp(heart_rate, 48, 150),
                temperature=clamp(temperature, 35.8, 40.2),
            )
        )

    return points


def target_vitals(profile: object, tick: int, spiking: bool) -> tuple[float, float, float]:
    if profile.simulation_pattern == "normal":
        spo2 = 98.2
        heart_rate = 76 + math.sin(tick * 0.25) * 2
        temperature = 36.9
    elif profile.simulation_pattern == "hypoxia":
        spo2 = 91.7 + math.sin(tick * 0.3) * 0.7
        heart_rate = 98 + math.cos(tick * 0.22) * 3
        temperature = 37.1
    elif profile.simulation_pattern == "fever":
        spo2 = 96.8
        heart_rate = 94 + math.sin(tick * 0.25) * 4
        temperature = 38.5 + math.cos(tick * 0.2) * 0.15
    elif profile.simulation_pattern == "cardiac":
        spo2 = 96.0
        heart_rate = 118 + math.sin(tick * 0.32) * 7
        temperature = 37.2
    elif profile.simulation_pattern == "sepsis":
        spo2 = 91.9 + math.sin(tick * 0.28) * 0.9
        heart_rate = 123 + math.cos(tick * 0.24) * 6
        temperature = 39.1 + math.sin(tick * 0.2) * 0.2
    else:
        improvement = min(tick, 20) * 0.08
        spo2 = 95.2 + improvement
        heart_rate = 92 - min(tick, 20) * 0.7
        temperature = 37.5 - min(tick, 20) * 0.04

    if spiking:
        if profile.simulation_pattern == "normal":
            heart_rate += 22
            spo2 -= 3
            temperature += 0.5
        elif profile.simulation_pattern == "hypoxia":
            spo2 -= 3.8
            heart_rate += 8
        elif profile.simulation_pattern == "fever":
            temperature += 0.7
            heart_rate += 7
        elif profile.simulation_pattern == "cardiac":
            heart_rate += 12
            spo2 -= 1.2
        elif profile.simulation_pattern == "sepsis":
            spo2 -= 2.8
            heart_rate += 10
            temperature += 0.5
        else:
            spo2 -= 1.4
            heart_rate += 10
            temperature += 0.3

    return spo2, heart_rate, temperature


def next_sample(profile: object, previous: VitalSample, tick: int, spiking: bool) -> VitalSample:
    target_spo2, target_heart_rate, target_temperature = target_vitals(profile, tick, spiking)

    return VitalSample(
        time=now_utc(),
        spo2=clamp(previous.spo2 + (target_spo2 - previous.spo2) * 0.34 + (random.random() - 0.5) * 0.8, 84, 100),
        heart_rate=clamp(previous.heart_rate + (target_heart_rate - previous.heart_rate) * 0.34 + (random.random() - 0.5) * 5, 48, 150),
        temperature=clamp(previous.temperature + (target_temperature - previous.temperature) * 0.34 + (random.random() - 0.5) * 0.12, 35.8, 40.2),
    )
