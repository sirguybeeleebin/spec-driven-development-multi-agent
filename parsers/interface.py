import re


def parse_interfaces(interfaces: str) -> list[dict[str, str]]:
    fences = re.findall(r"```", interfaces)
    blocks = re.findall(
        r"```([a-zA-Z0-9_+-]+)[ \t]*\n(.*?)\n```",
        interfaces,
        re.DOTALL,
    )

    if not blocks:
        raise ValueError("No interface code blocks found")

    if len(fences) != len(blocks) * 2:
        raise ValueError("Invalid interface code block")

    return [
        {
            "language": language,
            "code": code.strip(),
        }
        for language, code in blocks
    ]


def parse_interface(interface: str) -> dict[str, str | list[str]]:
    fqn = None
    language = None
    sections = {}
    current_section = None
    code = None
    inside_code = False

    for line in interface.splitlines():
        if line.startswith("```"):
            if not inside_code:
                if code is not None:
                    raise ValueError("Invalid interface code block")

                inside_code = True
                code = []
            else:
                inside_code = False

            continue

        if inside_code:
            code.append(line)
            continue

        fqn_match = re.fullmatch(r"## (.+)", line)
        language_match = re.fullmatch(r"### Language", line)
        section_match = re.fullmatch(
            r"### (Description|Steps|Returns|Interface)",
            line,
        )

        if fqn_match:
            if fqn is not None:
                raise ValueError("Duplicate FullQualifiedName")

            fqn = fqn_match.group(1).strip()
            current_section = None
            continue

        if language_match:
            if language is not None:
                raise ValueError("Duplicate Language")

            current_section = "Language"
            sections[current_section] = []
            continue

        if section_match:
            section = section_match.group(1)

            if section in sections:
                raise ValueError(f"Duplicate {section}")

            sections[section] = []
            current_section = section
            continue

        if current_section is not None:
            sections[current_section].append(line)

    if inside_code:
        raise ValueError("Invalid interface code block")

    if not fqn:
        raise ValueError("Missing or empty FullQualifiedName")

    if "Language" not in sections:
        raise ValueError("Missing or empty Language")

    language = "\n".join(sections["Language"]).strip()

    if not language:
        raise ValueError("Missing or empty Language")

    for section in ("Description", "Steps", "Returns"):
        if section not in sections or not "\n".join(sections[section]).strip():
            raise ValueError(f"Missing or empty {section}")

    if "Interface" not in sections:
        raise ValueError("Missing or empty Interface")

    if code is None or not "\n".join(code).strip():
        raise ValueError("Missing or empty code block")

    parsed_steps = []

    for line in sections["Steps"]:
        if not line.strip():
            continue

        match = re.fullmatch(r"\s*\d+\.\s+(.+)", line)

        if match is None:
            raise ValueError(f"Invalid interface step: {line.strip()}")

        parsed_steps.append(match.group(1).strip())

    if not parsed_steps:
        raise ValueError("Steps must contain at least one entry")

    return {
        "fqn": fqn,
        "language": language,
        "description": "\n".join(sections["Description"]).strip(),
        "steps": parsed_steps,
        "returns": "\n".join(sections["Returns"]).strip(),
        "code": "\n".join(code).strip(),
    }