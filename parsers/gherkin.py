import re


def parse_gherkins(gherkins: str) -> list[str]:
    scenarios = re.split(
        r"(?=^## Scenario:)",
        gherkins,
        flags=re.MULTILINE,
    )

    scenarios = [
        scenario.strip()
        for scenario in scenarios
        if scenario.strip() and scenario.lstrip().startswith("## Scenario:")
    ]

    if not scenarios:
        raise ValueError("No Gherkin scenarios found")

    if any(
        not re.match(r"^## Scenario:[ \t]*\S", scenario)
        for scenario in scenarios
    ):
        raise ValueError("Invalid Gherkin scenario heading")

    return scenarios


def parse_gherkin(gherkin: str) -> dict[str, str | list[str]]:
    name = re.search(
        r"^## Scenario:[ \t]*(.+)$",
        gherkin,
        re.MULTILINE,
    )

    if name is None:
        raise ValueError("Missing '## Scenario: <name>' heading")

    fqn_section = re.search(
        r"^### FQNs\s*\n(.*?)(?=^### |\Z)",
        gherkin,
        re.MULTILINE | re.DOTALL,
    )

    if fqn_section is None:
        raise ValueError("Missing '### FQNs' section")

    fqns = [
        line.strip().lstrip("-").strip().strip("`")
        for line in fqn_section.group(1).splitlines()
        if line.strip()
    ]

    if not fqns:
        raise ValueError("FullQualifiedNames section must contain at least one entry")

    gherkin_section = re.search(
        r"^### Gherkin\s*\n(.*)\Z",
        gherkin,
        re.MULTILINE | re.DOTALL,
    )

    if gherkin_section is None:
        raise ValueError("Missing '### Gherkin' section")

    blocks = re.findall(
        r"^```gherkin\s*\n(.*?)^```",
        gherkin_section.group(1),
        re.MULTILINE | re.DOTALL,
    )

    if len(blocks) != 1:
        raise ValueError("Scenario must contain exactly one Gherkin code block")

    steps = [
        line.strip()
        for line in blocks[0].splitlines()
        if line.strip()
    ]

    if not steps:
        raise ValueError("Gherkin code block cannot be empty")

    if not re.match(r"^Given\s+\S", steps[0]):
        raise ValueError("Scenario must start with Given")

    when_indices = [
        index
        for index, step in enumerate(steps)
        if re.match(r"^When\s+\S", step)
    ]

    if len(when_indices) != 1:
        raise ValueError("Scenario must contain exactly one When")

    then_indices = [
        index
        for index, step in enumerate(steps)
        if re.match(r"^Then\s+\S", step)
    ]

    if not then_indices:
        raise ValueError("Scenario must contain at least one Then")

    if when_indices[0] >= then_indices[0]:
        raise ValueError("When must appear before Then")

    for index, step in enumerate(steps):
        if re.match(r"^And\s+\S", step):
            if index == 0 or not re.match(
                r"^(Given|When|Then|And)\s+\S",
                steps[index - 1],
            ):
                raise ValueError(f"Invalid And step: {step}")
        elif not re.match(r"^(Given|When|Then)\s+\S", step):
            raise ValueError(f"Invalid Gherkin step: {step}")

    return {
        "name": name.group(1).strip(),
        "fqns": fqns,
        "gherkin": blocks[0].strip(),
    }