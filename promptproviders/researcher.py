from __future__ import annotations

import json

from models import Skill, State


class ResearcherPromptProvider:
    def __init__(
        self,
        *,
        system_template: str,
        user_template: str,
        final_prompt: str,
    ) -> None:
        self._system = system_template
        self._user = user_template
        self._final = final_prompt

    @property
    def system(self) -> str:
        return self._system

    @property
    def final_user(self) -> str:
        return self._final

    def format_user(
        self,
        state: State,
        skills: list[Skill],
    ) -> str:
        none = "_(none)_"
        task = state.task

        fqns = "\n".join(f"- `{fqn}`" for fqn in task.fqns) if task.fqns else none

        if task.interfaces:
            interface_parts = []

            for interface in task.interfaces:
                chunk = [
                    f"## Interface: {interface.name}",
                    f"Language: {interface.language}",
                ]

                if interface.description:
                    chunk.append(f"Description: {interface.description}")

                if interface.steps:
                    steps_text = "\n".join(
                        f"{number}. {step}"
                        for number, step in enumerate(interface.steps, start=1)
                    )
                    chunk.append(f"Steps:\n{steps_text}")

                chunk.append(f"```{interface.language}\n{interface.content}\n```")

                interface_parts.append("\n\n".join(chunk))

            interfaces = "\n\n".join(interface_parts)
        else:
            interfaces = none

        if task.gherkins:
            gherkin_parts = []

            for gherkin in task.gherkins:
                chunk = [
                    f"## Scenario: {gherkin.name}",
                    f"Target FQN: `{gherkin.fqn}`",
                    f"Test FQN: `{gherkin.test_fqn}`",
                ]

                for section, items in (
                    ("Given", gherkin.given),
                    ("When", gherkin.when),
                    ("Then", gherkin.then),
                ):
                    if items:
                        chunk.append(
                            f"### {section}\n"
                            + "\n".join(f"- {item}" for item in items)
                        )

                gherkin_parts.append("\n\n".join(chunk))

            gherkins = "\n\n".join(gherkin_parts)
        else:
            gherkins = none

        sequence = (
            none
            if task.sequence is None
            else (f"```{task.sequence.language}\n{task.sequence.content}\n```")
        )

        skills_catalog = (
            "\n\n".join(
                f"## Skill: {skill.name}\n\n{skill.description}" for skill in skills
            )
            if skills
            else none
        )

        return self._user.format(
            goal=task.goal or none,
            fqns=fqns,
            interfaces=interfaces,
            gherkins=gherkins,
            constitution=task.constitution or none,
            sequence=sequence,
            skills=skills_catalog,
        )

    def parse_final_response(
        self,
        final_response: str,
    ) -> dict:
        return json.loads(final_response)
