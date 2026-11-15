from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from models import Agents

AgentConfig = Mapping[str, Any]


@dataclass(frozen=True)
class Config:
    root: Path
    agent_configs: dict[Agents, AgentConfig]
    constitution: str
    skills: list[str]


def make_config(root: Path) -> Config:
    resolved_root = root.expanduser().resolve()

    config_path = resolved_root / "AGENT.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    constitution_path = resolved_root / "AGENT.md"
    constitution = (
        constitution_path.read_text(encoding="utf-8")
        if constitution_path.exists()
        else ""
    )

    skills: list[str] = []
    skills_dir = resolved_root / "skills"

    if skills_dir.is_dir():
        for skill_path in sorted(skills_dir.glob("*/SKILL.md")):
            skills.append(skill_path.read_text(encoding="utf-8"))

    agent_configs = {
        Agents(name): config for name, config in raw.get("agents", {}).items()
    }

    return Config(
        root=resolved_root,
        agent_configs=agent_configs,
        constitution=constitution,
        skills=skills,
    )
