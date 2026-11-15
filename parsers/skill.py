import re


_FRONTMATTER = re.compile(
    r"\A---[ \t]*\n(.*?)\n---[ \t]*\n",
    re.DOTALL,
)


def parse_skill(text: str) -> dict[str, str]:
    fm = _FRONTMATTER.match(text)

    if fm is None:
        raise ValueError("Skill: missing frontmatter block")

    meta: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for raw_line in fm.group(1).splitlines():
        if not raw_line.strip():
            continue

        if raw_line[0] not in (" ", "\t") and ":" in raw_line:
            if current_key is not None:
                meta[current_key] = " ".join(current_lines).strip()

            key, _, value = raw_line.partition(":")

            if not re.fullmatch(
                r"[a-zA-Z][a-zA-Z0-9_-]*",
                key.strip(),
            ):
                raise ValueError(f"Skill: invalid frontmatter key: {key.strip()}")

            current_key = key.strip()

            if current_key in meta:
                raise ValueError(f"Skill: duplicate frontmatter key: {current_key}")

            current_lines = [value.strip()]

        elif current_key is not None and raw_line.startswith(" "):
            current_lines.append(raw_line.strip())

        else:
            raise ValueError(f"Skill: invalid frontmatter line: {raw_line}")

    if current_key is not None:
        meta[current_key] = " ".join(current_lines).strip()

    for key in ("name", "description"):
        if key not in meta or not meta[key]:
            raise ValueError(f"Skill: missing or empty '{key}'")

    if not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*",
        meta["name"],
    ):
        raise ValueError("Skill: invalid name format")

    content = text[fm.end() :].strip()

    if not content:
        raise ValueError("Skill: content cannot be empty")

    return {
        "name": meta["name"],
        "description": meta["description"],
        "content": content,
    }