from __future__ import annotations

import json


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

    def format_user(self, context: dict) -> str:
        none = "_(none)_"

        current_gherkin = context["current_gherkin"]
        interfaces = context["interfaces"]
        tester_result = context["tester_result"]
        skills = context["skills"]

        if current_gherkin is None:
            gherkin = none
        else:
            fqns = (
                "\n".join(
                    f"- `{fqn['fqn']}` (role: `{fqn['role']}`)"
                    for fqn in current_gherkin["FullQualifiedNames"]
                )
                if current_gherkin["FullQualifiedNames"]
                else none
            )

            steps = "\n".join(
                [
                    *(f"Given {step}" for step in current_gherkin["given"]),
                    *(f"When {step}" for step in current_gherkin["when"]),
                    *(f"Then {step}" for step in current_gherkin["then"]),
                ]
            )

            gherkin = (
                f"## Scenario: {current_gherkin['name']}\n\n"
                f"### FQNs\n{fqns}\n\n"
                f"### Gherkin\n```gherkin\n{steps}\n```"
            )

        interfaces_text = (
            "\n\n".join(
                "\n".join(
                    [
                        f"## Interface: `{interface['fqn']['fqn']}`",
                        f"FullQualifiedName Role: `{interface['fqn']['role']}`",
                        f"Language: {interface['language']}",
                        f"```{interface['language']}",
                        interface["content"],
                        "```",
                    ]
                )
                for interface in interfaces
            )
            if interfaces
            else none
        )

        skills_catalog = (
            "\n\n".join(
                f"## Skill: {skill['name']}\n\n{skill['description']}"
                for skill in skills
            )
            if skills
            else none
        )

        return self._user.format(
            current_gherkin=gherkin,
            interfaces=interfaces_text,
            testrunner_results=(
                json.dumps(
                    tester_result,
                    ensure_ascii=False,
                    indent=2,
                )
                if tester_result
                else none
            ),
            skills=skills_catalog,
        )

    @property
    def final_user(self) -> str:
        return self._final

    def parse_final_response(self, final_response: str) -> dict:
        return json.loads(final_response)