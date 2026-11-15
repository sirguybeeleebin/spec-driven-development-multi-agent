from __future__ import annotations

import json
import traceback
from typing import Protocol

from models import AgentResult, Message, Metric, Role, Skill, State, ToolCall


class Tool(Protocol):
    def get_openai_schema(self) -> dict: ...
    def execute(self, args: dict) -> dict: ...


class Guardrail(Protocol):
    def check(
        self,
        *,
        state: State,
        tool_call: ToolCall,
    ) -> None: ...


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[Message],
        tools: list[Tool],
    ) -> tuple[Message, list[Metric]]: ...


class PromptProvider(Protocol):
    @property
    def system(self) -> str: ...

    def format_user(
        self,
        state: State,
        skills: list[Skill],
    ) -> str: ...

    @property
    def final_user(self) -> str: ...

    def parse_final_response(
        self,
        final_response: str,
    ) -> dict: ...


class AgentFSM(Protocol):
    def reset(self) -> None: ...
    def mark_running(self) -> None: ...
    def mark_success(self) -> None: ...
    def mark_error(self) -> None: ...


class AgentRunner:
    def __init__(
        self,
        *,
        llm: LLMClient,
        agent_fsm: AgentFSM,
        guardrails: list[Guardrail],
        prompt_provider: PromptProvider,
        skills: list[Skill],
        tools: list[Tool],
        max_iterations: int,
    ) -> None:
        self._llm = llm
        self._agent_fsm = agent_fsm
        self._guardrails = guardrails
        self._prompt_provider = prompt_provider
        self._skills = skills
        self._tools = tools
        self._max_iterations = max_iterations

        print(
            f"[AgentRunner] Initialized: "
            f"skills={len(skills)}, "
            f"tools={len(tools)}, "
            f"max_iterations={max_iterations}"
        )

    def run(self, *, state: State) -> AgentResult:
        self._agent_fsm.reset()
        self._agent_fsm.mark_running()

        try:
            print("[AgentRunner] Starting execution")
            print("[AgentRunner] Building initial session")

            session = [
                Message(
                    role=Role.SYSTEM,
                    content=self._prompt_provider.system,
                ),
                Message(
                    role=Role.USER,
                    content=self._prompt_provider.format_user(
                        state,
                        self._skills,
                    ),
                ),
            ]

            print(f"[AgentRunner] Initial session created: messages={len(session)}")

            metrics = []
            tools_by_name = {
                tool.get_openai_schema()["function"]["name"]: tool
                for tool in self._tools
            }

            print(f"[AgentRunner] Available tools: {list(tools_by_name)}")

            for iteration in range(self._max_iterations):
                print(f"[AgentRunner] Iteration {iteration + 1}/{self._max_iterations}")
                print(f"[AgentRunner] Sending {len(session)} messages to LLM")

                reply, reply_metrics = self._llm.complete(session, self._tools)
                session.append(reply)
                metrics.append(reply_metrics)

                print(
                    f"[AgentRunner] LLM response received: "
                    f"tool_calls={len(reply.tool_calls or [])}"
                )

                if not reply.tool_calls:
                    print(
                        "[AgentRunner] LLM returned no tool calls. Stopping execution."
                    )
                    break

                for tool_call in reply.tool_calls:
                    print(
                        f"[AgentRunner] Executing tool: name={tool_call.name}, id={tool_call.id}"
                    )
                    print(f"[AgentRunner] Tool arguments: {tool_call.arguments}")

                    tool = tools_by_name[tool_call.name]

                    try:
                        for guardrail in self._guardrails:
                            guardrail.check(
                                state=state,
                                tool_call=tool_call,
                            )

                        result = tool.execute(tool_call.arguments)

                        print(
                            f"[AgentRunner] Tool execution succeeded: {tool_call.name}"
                        )
                        print(f"[AgentRunner] Tool result: {result}")
                    except Exception as exc:
                        print(
                            f"[AgentRunner] Tool execution failed: "
                            f"name={tool_call.name}, "
                            f"error={type(exc).__name__}: {exc}"
                        )
                        traceback.print_exc()

                        result = {
                            "ok": False,
                            "error": type(exc).__name__,
                            "message": str(exc),
                            "traceback": traceback.format_exc(),
                        }

                    session.append(
                        Message(
                            role=Role.TOOL,
                            content=json.dumps(
                                result,
                                ensure_ascii=False,
                                default=str,
                            ),
                            tool_call_id=tool_call.id,
                        )
                    )

                    print(
                        f"[AgentRunner] Tool result added to session: tool_call_id={tool_call.id}"
                    )

            print(
                f"[AgentRunner] Main loop completed: "
                f"messages={len(session)}, "
                f"iterations={len(metrics)}"
            )

            print("[AgentRunner] Appending final prompt")

            session.append(
                Message(
                    role=Role.USER,
                    content=self._prompt_provider.final_user,
                )
            )

            print("[AgentRunner] Requesting final response")

            final_reply, final_metrics = self._llm.complete(session, [])

            session.append(final_reply)
            metrics.append(final_metrics)

            print(
                f"[AgentRunner] Final response received: "
                f"content_length={len(final_reply.content)}"
            )

            response = self._prompt_provider.parse_final_response(final_reply.content)

            print(
                f"[AgentRunner] Execution completed: "
                f"response_keys={list(response)}, "
                f"total_metric_batches={len(metrics)}"
            )

            result = AgentResult(
                response=response,
                messages=session,
                metrics=metrics,
            )

            self._agent_fsm.mark_success()

            return result
        except Exception:
            self._agent_fsm.mark_error()
            raise
