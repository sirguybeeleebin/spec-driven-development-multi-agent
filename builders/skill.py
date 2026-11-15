from models import Skill


def build_skills(skills: list[dict[str, str]]) -> list[Skill]:
    return [
        Skill(
            name=skill["name"],
            description=skill["description"],
            content=skill["content"],
        )
        for skill in skills
    ]