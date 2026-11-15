from models import (
    FullQualifiedName,
    FullQualifiedNameRole,
    Gherkin,
    Interface,
    Sequence,
    SequenceArrow,
    SequenceBranch,
    SequenceDirective,
    SequenceFragment,
    SequenceFragmentType,
    SequenceMessage,
    SequenceNote,
    SequenceNotePosition,
    SequenceParticipant,
    SequenceParticipantType,
    Task,
)


def build_task(
    *,
    task_id: str,
    goal: str,
    fqns: list[dict[str, str | int]],
    interfaces: list[dict[str, str | list[str]]],
    participants: list[dict[str, object]],
    components: list[dict[str, object]],
    gherkins: list[dict[str, str | list[str]]],
) -> Task:
    fqns_by_name = {
        item["fqn"]: FullQualifiedName(
            fqn=item["fqn"],
            role=FullQualifiedNameRole(item["role"]),
        )
        for item in fqns
    }

    return Task(
        task_id=task_id,
        goal=goal,
        fqns=list(fqns_by_name.values()),
        interfaces=[
            Interface(
                fqn=fqns_by_name[interface["fqn"]],
                language=interface["language"],
                content=interface["code"],
            )
            for interface in interfaces
        ],
        sequence=Sequence(
            participants=[
                SequenceParticipant(
                    alias=participant["alias"],
                    name=participant["name"],
                    type=SequenceParticipantType(participant["type"]),
                    fqn=fqns_by_name.get(participant.get("fqn")),
                )
                for participant in participants
            ],
            components=[
                SequenceMessage(
                    source=component["source"],
                    target=component["target"],
                    arrow=SequenceArrow(component["arrow"]),
                    content=component["content"],
                )
                if component["type"] == "message"
                else SequenceNote(
                    position=SequenceNotePosition(component["position"]),
                    participants=component["participants"],
                    content=component["content"],
                )
                if component["type"] == "note"
                else SequenceFragment(
                    type=SequenceFragmentType(component["fragment_type"]),
                    branches=[
                        SequenceBranch(
                            condition=branch["condition"],
                            components=[
                                SequenceMessage(
                                    source=nested["source"],
                                    target=nested["target"],
                                    arrow=SequenceArrow(nested["arrow"]),
                                    content=nested["content"],
                                )
                                if nested["type"] == "message"
                                else SequenceNote(
                                    position=SequenceNotePosition(nested["position"]),
                                    participants=nested["participants"],
                                    content=nested["content"],
                                )
                                if nested["type"] == "note"
                                else SequenceDirective(name=nested["name"])
                                for nested in branch["components"]
                            ],
                        )
                        for branch in component["branches"]
                    ],
                )
                if component["type"] == "fragment"
                else SequenceDirective(name=component["name"])
                for component in components
            ],
        ),
        gherkins=[
            Gherkin(
                name=gherkin["name"],
                FullQualifiedNames=[
                    fqns_by_name[fqn]
                    for fqn in gherkin["FullQualifiedNames"]
                ],
                given=gherkin["given"],
                when=gherkin["when"],
                then=gherkin["then"],
            )
            for gherkin in gherkins
        ],
    )