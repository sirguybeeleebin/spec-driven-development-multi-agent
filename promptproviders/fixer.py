from __future__ import annotations

import json

from models import Agents, Skill, State


class FixerPromptProvider:
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

        current = state.current_gherkin

        if current is None:
            current_gherkin = none
        else:
            gherkin_lines = [
                *(f"Given {step}" for step in current.given),
                *(f"When {step}" for step in current.when),
                *(f"Then {step}" for step in current.then),
            ]
            steps = "\n".join(gherkin_lines)

            current_gherkin = (
                f"## Scenario: {current.name}\n\n"
                f"### FQN: {current.fqn}\n\n"
                f"### Test FQN: {current.test_fqn}\n\n"
                f"### Gherkin\n\n"
                f"```gherkin\n{steps}\n```"
            )

        tester_results = state.agent_results[Agents.TESTER]
        tester_result = tester_results[-1].response if tester_results else {}

        return self._user.format(
            current_gherkin=current_gherkin,
            testrunner_results=(
                json.dumps(
                    tester_result,
                    ensure_ascii=False,
                    indent=2,
                )
                if tester_result
                else none
            ),
            skills="\n\n".join(str(skill) for skill in skills) or none,
        )

    @property
    def final_user(self) -> str:
        return self._final

    def parse_final_response(
        self,
        final_response: str,
    ) -> dict:
        return json.loads(final_response)
