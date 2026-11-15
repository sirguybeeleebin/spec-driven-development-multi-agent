from __future__ import annotations

import re

from models import FullQualifiedName, Gherkin, Interface, Sequence, Task

_SECTION = re.compile(r"^# (?!#)([^\n]+?)\s*$", re.MULTILINE)
_GHERKIN_HEAD = re.compile(r"^## Scenario:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
_GHERKIN_FQN = re.compile(r"^### FQN:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
_GHERKIN_TEST_FQN = re.compile(r"^### Test FQN:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
_GHERKIN_BLOCK = re.compile(r"^### Gherkin[ \t]*$", re.MULTILINE)
_INTERFACE_HEAD = re.compile(r"^## FQN:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
_HEADER_SCALAR = re.compile(r"^\s*-\s*(\w+):\s*(.+)$")
_LANG_TAG = re.compile(
    r"```([^\s`]+)[ \t]*\r?\n(.*?)\r?\n```",
    re.DOTALL,
)
_GHERKIN_FENCE = re.compile(
    r"```gherkin[ \t]*\r?\n(.*?)\r?\n```",
    re.DOTALL,
)
_MERMAID_FENCE = re.compile(
    r"```mermaid[ \t]*\r?\n(.*?)\r?\n```",
    re.DOTALL,
)
_PLANTUML_FENCE = re.compile(
    r"```plantuml[ \t]*\r?\n(.*?)\r?\n```",
    re.DOTALL,
)
_GHERKIN_LINE = re.compile(r"^(Given|When|Then|And)\s+(.+)$")
_DESCRIPTION = re.compile(
    r"Description:[ \t]*\r?\n((?:[ \t]+(?!Steps:)\S.*(?:\r?\n|$))+)"
)
_STEPS = re.compile(r"Steps:[ \t]*\r?\n((?:[ \t]+\d+\..*(?:\r?\n|$))+)")
_STEP_LINE = re.compile(r"^\d+\.\s+(.+)$")


def parse_task(text: str, constitution: str) -> Task:
    if not constitution:
        raise ValueError("task: constitution is empty")

    section_matches = list(_SECTION.finditer(text))
    sections: dict[str, str] = {}

    for i, match in enumerate(section_matches):
        name = match.group(1).strip()
        start = match.end()
        end = (
            section_matches[i + 1].start()
            if i + 1 < len(section_matches)
            else len(text)
        )
        sections[name] = text[start:end]

    for required in ("Task", "Goal", "Interfaces", "Gherkins"):
        if required not in sections:
            raise ValueError(f"missing '# {required}' section")

    header: dict[str, str] = {}

    for raw_line in sections["Task"].splitlines():
        match = _HEADER_SCALAR.match(raw_line)
        if match:
            header[match.group(1)] = match.group(2).strip()

    if "task_id" not in header:
        raise ValueError("task: missing 'task_id'")
    if not header["task_id"]:
        raise ValueError("task: 'task_id' is empty")

    task_id = header["task_id"]

    goal = sections["Goal"].strip()
    if not goal:
        raise ValueError(f"task {task_id!r}: goal is empty")

    interfaces_body = sections["Interfaces"]
    interface_headers = list(_INTERFACE_HEAD.finditer(interfaces_body))

    if not interface_headers:
        raise ValueError("no interfaces declared")

    fqns: list[FullQualifiedName] = []
    interfaces: list[Interface] = []
    seen_fqns: set[FullQualifiedName] = set()
    short_to_fqn: dict[str, FullQualifiedName] = {}

    for i, match in enumerate(interface_headers):
        fqn_value = match.group(1).strip()
        if not fqn_value:
            raise ValueError("interface: FQN is empty")

        fqn = FullQualifiedName(fqn_value)

        if fqn in seen_fqns:
            raise ValueError(f"fqn: duplicate entry {fqn!s}")

        if fqn.short_name in short_to_fqn:
            raise ValueError(
                f"fqn: short name {fqn.short_name!r} appears in both "
                f"{short_to_fqn[fqn.short_name]!s} and {fqn!s}"
            )

        seen_fqns.add(fqn)
        short_to_fqn[fqn.short_name] = fqn
        fqns.append(fqn)

        start = match.end()
        end = (
            interface_headers[i + 1].start()
            if i + 1 < len(interface_headers)
            else len(interfaces_body)
        )
        interface_body = interfaces_body[start:end]

        fences = list(_LANG_TAG.finditer(interface_body))
        if len(fences) != 1:
            raise ValueError(
                f"interface {fqn!s}: expected exactly one fenced block, "
                f"got {len(fences)}"
            )

        fence = fences[0]
        language = fence.group(1).strip().lower()
        content = fence.group(2)

        if not content.strip():
            raise ValueError(f"interface {fqn!s}: content is empty")

        desc_match = _DESCRIPTION.search(content)
        if desc_match is None:
            description = ""
        else:
            description = " ".join(
                line.strip()
                for line in desc_match.group(1).splitlines()
                if line.strip()
            )

        steps_match = _STEPS.search(content)
        steps: list[str] = []

        if steps_match is not None:
            for line in steps_match.group(1).splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                step_match = _STEP_LINE.match(stripped)
                if step_match:
                    steps.append(step_match.group(1).strip())

        interfaces.append(
            Interface(
                name=fqn.short_name,
                language=language,
                content=content,
                description=description,
                steps=steps,
            )
        )

    gherkins: list[Gherkin] = []
    gherkins_body = sections["Gherkins"]
    gherkins_matches = list(_GHERKIN_HEAD.finditer(gherkins_body))

    if not gherkins_matches:
        raise ValueError("no gherkins declared")

    seen_gherkins: set[str] = set()
    seen_test_fqns: set[FullQualifiedName] = set()

    for i, match in enumerate(gherkins_matches):
        name = match.group(1).strip()

        if not name:
            raise ValueError("gherkin: empty name")
        if name in seen_gherkins:
            raise ValueError(f"gherkin: duplicate name {name!r}")

        seen_gherkins.add(name)

        start = match.end()
        end = (
            gherkins_matches[i + 1].start()
            if i + 1 < len(gherkins_matches)
            else len(gherkins_body)
        )
        body = gherkins_body[start:end]

        fqn_matches = list(_GHERKIN_FQN.finditer(body))
        if len(fqn_matches) != 1:
            raise ValueError(
                f"gherkin {name!r}: expected exactly one FQN, got {len(fqn_matches)}"
            )

        fqn_value = fqn_matches[0].group(1).strip()
        if not fqn_value:
            raise ValueError(f"gherkin {name!r}: FQN is empty")

        fqn = FullQualifiedName(fqn_value)

        if fqn not in seen_fqns:
            raise ValueError(
                f"gherkin {name!r}: FQN {fqn!s} is not declared in '# Interfaces'"
            )

        test_fqn_matches = list(_GHERKIN_TEST_FQN.finditer(body))
        if len(test_fqn_matches) != 1:
            raise ValueError(
                f"gherkin {name!r}: expected exactly one Test FQN, "
                f"got {len(test_fqn_matches)}"
            )

        test_fqn_value = test_fqn_matches[0].group(1).strip()
        if not test_fqn_value:
            raise ValueError(f"gherkin {name!r}: Test FQN is empty")

        test_fqn = FullQualifiedName(test_fqn_value)

        if test_fqn in seen_test_fqns:
            raise ValueError(f"gherkin: duplicate Test FQN {test_fqn!s}")

        seen_test_fqns.add(test_fqn)

        gherkin_blocks = list(_GHERKIN_BLOCK.finditer(body))
        if len(gherkin_blocks) != 1:
            raise ValueError(
                f"gherkin {name!r}: expected exactly one "
                f"'### Gherkin' section, got {len(gherkin_blocks)}"
            )

        fence = _GHERKIN_FENCE.search(body[gherkin_blocks[0].end() :])
        if fence is None:
            raise ValueError(f"gherkin {name!r} missing ```gherkin``` block")

        given: list[str] = []
        when: list[str] = []
        then: list[str] = []
        current: list[str] | None = None

        for raw_line in fence.group(1).splitlines():
            line = raw_line.strip()
            if not line:
                continue

            step_match = _GHERKIN_LINE.match(line)
            if step_match is None:
                raise ValueError(f"gherkin {name!r} line without keyword: {line!r}")

            keyword = step_match.group(1)
            rest = step_match.group(2)

            if keyword == "Given":
                current = given
                given.append(rest)
            elif keyword == "When":
                current = when
                when.append(rest)
            elif keyword == "Then":
                current = then
                then.append(rest)
            elif keyword == "And":
                if current is None:
                    raise ValueError(
                        f"gherkin {name!r} 'And' without preceding keyword"
                    )
                current.append(rest)

        if not given:
            raise ValueError(f"gherkin {name!r} has no Given step")
        if not when:
            raise ValueError(f"gherkin {name!r} has no When step")
        if not then:
            raise ValueError(f"gherkin {name!r} has no Then step")

        gherkins.append(
            Gherkin(
                name=name,
                fqn=fqn,
                test_fqn=test_fqn,
                given=given,
                when=when,
                then=then,
            )
        )

    sequence: Sequence | None = None

    if "Sequence" in sections:
        sequence_body = sections["Sequence"]
        mermaid = _MERMAID_FENCE.search(sequence_body)
        plantuml = _PLANTUML_FENCE.search(sequence_body)

        if mermaid is not None:
            content = mermaid.group(1).strip()
            if not content:
                raise ValueError("sequence: mermaid content is empty")
            sequence = Sequence(language="mermaid", content=content)
        elif plantuml is not None:
            content = plantuml.group(1).strip()
            if not content:
                raise ValueError("sequence: plantuml content is empty")
            sequence = Sequence(language="plantuml", content=content)
        else:
            raise ValueError(
                "# Sequence section has no ```mermaid``` or ```plantuml``` block"
            )

    return Task(
        task_id=task_id,
        goal=goal,
        fqns=fqns,
        interfaces=interfaces,
        gherkins=gherkins,
        constitution=constitution,
        sequence=sequence,
    )
