from __future__ import annotations

import json
import re
from uuid import uuid4


class QwenResponseParser:
    _TOOL_CALL = re.compile(
        r"<tool_call>\s*(.*?)\s*</tool_call>",
        re.DOTALL,
    )

    def parse(self, response: dict) -> dict:
        if response.get("tool_calls"):
            return response

        content = response.get("content") or ""
        tool_calls: list[dict] = []

        for match in self._TOOL_CALL.finditer(content):
            try:
                call = json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

            if not isinstance(call, dict):
                continue

            function_name = call.get("name")
            arguments = call.get("arguments", {})

            if not isinstance(function_name, str):
                continue

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    continue

            if not isinstance(arguments, dict):
                continue

            tool_calls.append(
                {
                    "id": f"call_{uuid4().hex}",
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "arguments": json.dumps(
                            arguments,
                            ensure_ascii=False,
                        ),
                    },
                }
            )

        if not tool_calls:
            return response

        response["content"] = self._TOOL_CALL.sub("", content).strip() or None
        response["tool_calls"] = tool_calls

        return response
