"""
Synthetic event generation package for Project 07 Red Analytics.
"""

from .base import BaseSyntheticGenerator
from .p4_generator import P4C2Generator
from .p5_generator import P5ShellGenerator
from .p6_generator import P6ExfilGenerator
from .scenarios import generate_normal_scenario, generate_stalled_scenario

__all__ = [
    "BaseSyntheticGenerator",
    "P4C2Generator",
    "P5ShellGenerator",
    "P6ExfilGenerator",
    "generate_normal_scenario",
    "generate_stalled_scenario",
]
