from __future__ import annotations

import json

from models import Skill, State


class TesterPromptProvider:
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

    def format_user(
        self,
        state: State,
        skills: list[Skill],
    ) -> str:
        none = "_(none)_"
        task = state.task

        current_gherkin = state.current_gherkin

        if current_gherkin is None:
            gherkin = none
        else:
            gherkin_lines = [
                *(f"Given {step}" for step in current_gherkin.given),
                *(f"When {step}" for step in current_gherkin.when),
                *(f"Then {step}" for step in current_gherkin.then),
            ]
            steps = "\n".join(gherkin_lines)

            gherkin = (
                f"## Scenario: {current_gherkin.name}\n\n"
                f"### FQN: {current_gherkin.fqn}\n\n"
                f"### Test FQN: {current_gherkin.test_fqn}\n\n"
                f"### Gherkin\n\n"
                f"```gherkin\n{steps}\n```"
            )

        interface_parts: list[str] = []

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

        interfaces = "\n\n".join(interface_parts) if interface_parts else none

        sequence = (
            f"```{task.sequence.language}\n{task.sequence.content}\n```"
            if task.sequence is not None
            else none
        )

        skills_catalog = (
            "\n\n".join(
                f"## Skill: {skill.name}\n\n{skill.description}" for skill in skills
            )
            if skills
            else none
        )

        return self._user.format(
            current_gherkin=gherkin,
            interfaces=interfaces,
            sequence=sequence,
            skills=skills_catalog,
        )

    @property
    def final_user(self) -> str:
        return self._final

    def parse_final_response(
        self,
        final_response: str,
    ) -> dict:
        return json.loads(final_response)
