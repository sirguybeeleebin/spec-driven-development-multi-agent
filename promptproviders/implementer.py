from __future__ import annotations

import json

from models import Agents, Skill, State


class ImplementerPromptProvider:
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

        fqn_by_short_name = {fqn.short_name: fqn for fqn in task.fqns}

        current_interface = state.current_interface

        current_fqn = (
            str(
                fqn_by_short_name.get(
                    current_interface.name,
                    current_interface.name,
                )
            )
            if current_interface is not None
            else none
        )

        target_file = (
            str(state.current_target_file)
            if state.current_target_file is not None
            else none
        )

        def format_interface(interface) -> str:
            fqn = fqn_by_short_name.get(interface.name)
            title = str(fqn) if fqn is not None else interface.name

            chunk = [
                f"## Interface: {title}",
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

            return "\n\n".join(chunk)

        current_interface_text = (
            format_interface(current_interface)
            if current_interface is not None
            else none
        )

        interfaces = (
            "\n\n".join(format_interface(interface) for interface in task.interfaces)
            if task.interfaces
            else none
        )

        sequence = (
            f"```{task.sequence.language}\n{task.sequence.content}\n```"
            if task.sequence is not None
            else none
        )

        researcher_results = (
            state.agent_results[Agents.RESEARCHER][-1].response
            if state.agent_results[Agents.RESEARCHER]
            else {}
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
            current_fqn=current_fqn,
            target_file=target_file,
            current_interface=current_interface_text,
            interfaces=interfaces,
            constitution=task.constitution or none,
            sequence=sequence,
            researcher_results=json.dumps(
                researcher_results,
                ensure_ascii=False,
                indent=2,
            ),
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
