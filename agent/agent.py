from __future__ import annotations

import json
import sys
import traceback
from typing import Protocol

from openai.types.chat import ChatCompletionMessageParam

from models import AgentStatus, Role
from tools import LoadSkillTool


class Tool(Protocol):
    @property
    def name(self) -> str: ...
    def get_openai_schema(self) -> dict: ...
    def execute(self, args: dict) -> dict: ...


class Guardrail(Protocol):
    def check(self, *, tool_call: dict) -> None: ...


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> tuple[dict, dict]: ...


class PromptProvider(Protocol):
    @property
    def system(self) -> str: ...

    def format_user(self, context: dict, skills: list[dict]) -> str: ...

    @property
    def final_user(self) -> str: ...

    def parse_final_response(self, final_response: str) -> dict: ...


class AgentFSM(Protocol):
    @property
    def status(self) -> AgentStatus: ...
    def reset(self) -> None: ...
    def mark_running(self) -> None: ...
    def mark_success(self) -> None: ...
    def mark_error(self) -> None: ...


class Agent:
    def __init__(
        self,
        *,
        llm: LLMClient,
        agent_fsm: AgentFSM,
        prompt_provider: PromptProvider,
        tools: list[Tool],
        guardrails: list[Guardrail],
        max_iterations: int,
    ) -> None:
        self._llm = llm
        self._agent_fsm = agent_fsm
        self._prompt_provider = prompt_provider
        self._tools = {tool.name: tool for tool in tools}
        self._guardrails = guardrails
        self._max_iterations = max_iterations

    def run(self, context: dict, skills: list[dict]) -> dict:
        session: list[ChatCompletionMessageParam] = []
        metrics: list[dict] = []

        self._agent_fsm.reset()
        self._agent_fsm.mark_running()

        try:
            print("[Agent] Starting execution", file=sys.stderr)

            tools = [
                *self._tools.values(),
                LoadSkillTool(skills=skills),
            ]
            tools_by_name = {
                tool.name: tool
                for tool in tools
            }
            tool_schemas = [
                tool.get_openai_schema()
                for tool in tools
            ]

            session = [
                {
                    "role": str(Role.SYSTEM),
                    "content": self._prompt_provider.system,
                },
                {
                    "role": str(Role.USER),
                    "content": self._prompt_provider.format_user(
                        context,
                        skills,
                    ),
                },
            ]

            print(
                f"[Agent] Initial session created: messages={len(session)}",
                file=sys.stderr,
            )

            for iteration in range(self._max_iterations):
                print(
                    f"[Agent] Iteration {iteration + 1}/{self._max_iterations}",
                    file=sys.stderr,
                )

                reply, reply_metrics = self._llm.complete(
                    session,
                    tools=tool_schemas,
                )

                session.append(reply)
                metrics.append(reply_metrics)

                tool_calls = reply.get("tool_calls", [])

                if not tool_calls:
                    break

                for tool_call in tool_calls:
                    function = tool_call["function"]
                    tool_name = function["name"]
                    tool_call_id = tool_call["id"]

                    tool = tools_by_name.get(tool_name)

                    if tool is None:
                        raise ValueError(f"Unknown tool: {tool_name}")

                    try:
                        for guardrail in self._guardrails:
                            guardrail.check(tool_call=tool_call)

                        args = json.loads(function["arguments"])
                        result = tool.execute(args)
                        content = json.dumps(result, ensure_ascii=False)

                    except Exception:
                        content = traceback.format_exc()

                    session.append(
                        {
                            "role": str(Role.TOOL),
                            "tool_call_id": tool_call_id,
                            "content": content,
                        }
                    )

            print(
                f"[Agent] Main loop completed: messages={len(session)}, iterations={len(metrics)}",
                file=sys.stderr,
            )

            session.append(
                {
                    "role": str(Role.USER),
                    "content": self._prompt_provider.final_user,
                }
            )

            final_reply, final_metrics = self._llm.complete(session)

            session.append(final_reply)
            metrics.append(final_metrics)

            final_content = final_reply.get("content") or ""
            response = self._prompt_provider.parse_final_response(final_content)

            self._agent_fsm.mark_success()

            print(
                f"[Agent] Execution completed: response_keys={list(response)}, metrics={metrics}",
                file=sys.stderr,
            )

            return {
                "response": response,
                "messages": session,
                "metrics": metrics,
                "status": self._agent_fsm.status,
            }

        except Exception as exc:
            print(
                f"[Agent] Execution failed: error={type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)

            self._agent_fsm.mark_error()

            return {
                "response": {},
                "messages": session,
                "metrics": metrics,
                "status": self._agent_fsm.status,
            }