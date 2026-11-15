from __future__ import annotations

import argparse
import json
import signal
import sys
import traceback
from collections.abc import Callable
from dataclasses import asdict, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

import yaml

from commands import (
    run_agent_fixer_command,
    run_agent_implementer_command,
    run_agent_researcher_command,
    run_agent_tester_command,
    run_config_delete_command,
    run_config_get_command,
    run_config_prune_command,
    run_config_set_command,
    run_config_show_command,
    run_create_fqns_command,
    run_create_gherkins_command,
    run_create_goal_command,
    run_create_interfaces_command,
    run_create_sequence_command,
    run_info_command,
    run_init_command,
    run_task_command,
    run_workflow_command,
)
from models import (
    Gherkin,
    Interface,
    Sequence,
    Skill,
    fqn,
)

CLI_VERSION = "1.0.0"

termination_signal = signal.SIGINT


class CLIArgumentError(Exception):
    pass


class InvalidRequestError(Exception):
    pass


class StdinReader:
    def read(self) -> dict[str, object]:
        raw = sys.stdin.read()

        if not raw.strip():
            raise InvalidRequestError("Входные данные отсутствуют")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise InvalidRequestError(f"Некорректный JSON: {error}") from error

        if not isinstance(data, dict):
            raise InvalidRequestError("Входные данные должны быть JSON-объектом")

        return data


class StdoutWriter:
    def write(self, data: object) -> None:
        sys.stdout.write(
            json.dumps(
                self.serialize(data),
                ensure_ascii=False,
            )
            + "\n"
        )
        sys.stdout.flush()

    def success(self, data: object) -> None:
        self.write(
            {
                "success": True,
                "data": data,
            }
        )

    def failure(
        self,
        *,
        error_type: str,
        message: str,
        code: str,
    ) -> None:
        self.write(
            {
                "success": False,
                "error": {
                    "type": error_type,
                    "code": code,
                    "message": message,
                },
            }
        )

    def serialize(self, value: object) -> object:
        if isinstance(value, Enum):
            return self.serialize(value.value)

        if isinstance(value, Path):
            return str(value)

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return str(value)

        if is_dataclass(value) and not isinstance(value, type):
            return self.serialize(asdict(value))

        if isinstance(value, dict):
            return {str(key): self.serialize(item) for key, item in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [self.serialize(item) for item in value]

        if hasattr(value, "model_dump"):
            return self.serialize(value.model_dump())

        if hasattr(value, "__dict__"):
            return self.serialize(vars(value))

        return value


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CLIArgumentError(message)


def handle_signal(signum: int, frame: object) -> None:
    global termination_signal

    termination_signal = signum
    raise KeyboardInterrupt


def make_model(model: type, value: object) -> object:
    if not isinstance(value, dict):
        raise InvalidRequestError(f"Ожидался JSON-объект для {model.__name__}")

    model_fields = {field.name for field in fields(model)}

    return model(**{key: item for key, item in value.items() if key in model_fields})


def make_models(model: type, value: object) -> list:
    if not isinstance(value, list):
        raise InvalidRequestError(f"Ожидался JSON-массив для {model.__name__}")

    return [make_model(model, item) for item in value]


def prepare_agent_input(
    agent: str,
    data: dict[str, object],
) -> dict[str, object]:
    if agent == "researcher":
        data["FullQualifiedNames"] = make_models(
            fqn,
            data["FullQualifiedNames"],
        )
        data["interfaces"] = make_models(
            Interface,
            data["interfaces"],
        )

        if data.get("sequence") is not None:
            data["sequence"] = make_model(
                Sequence,
                data["sequence"],
            )

    elif agent == "implementer":
        data["current_fqn"] = make_model(
            fqn,
            data["current_fqn"],
        )
        data["current_interface"] = make_model(
            Interface,
            data["current_interface"],
        )
        data["interfaces"] = make_models(
            Interface,
            data["interfaces"],
        )
        data["skills"] = make_models(
            Skill,
            data["skills"],
        )

        if data.get("sequence") is not None:
            data["sequence"] = make_model(
                Sequence,
                data["sequence"],
            )

    elif agent in {"tester", "fixer"}:
        data["current_gherkin"] = make_model(
            Gherkin,
            data["current_gherkin"],
        )
        data["interfaces"] = make_models(
            Interface,
            data["interfaces"],
        )
        data["skills"] = make_models(
            Skill,
            data["skills"],
        )

        if data.get("sequence") is not None:
            data["sequence"] = make_model(
                Sequence,
                data["sequence"],
            )

    return data


def validate_project(root: Path) -> dict[str, object]:
    required_paths = [
        root / "AGENT.yaml",
        root / "AGENT.md",
        root / "tasks",
        root / "workflows",
        root / "skills",
        root / "data",
    ]

    missing = [str(path) for path in required_paths if not path.exists()]

    if missing:
        return {
            "valid": False,
            "errors": [f"Отсутствует обязательный путь: {path}" for path in missing],
        }

    config_path = root / "AGENT.yaml"

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return {
            "valid": False,
            "errors": [f"Некорректный AGENT.yaml: {error}"],
        }

    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["AGENT.yaml должен содержать YAML-объект"],
        }

    return {
        "valid": True,
        "errors": [],
    }


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="sddma")

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser("info")
    subparsers.add_parser("init")
    subparsers.add_parser("validate")

    config_parser = subparsers.add_parser("config")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command",
        required=True,
    )

    config_set = config_subparsers.add_parser("set")
    config_set.add_argument("key")
    config_set.add_argument("value")

    config_get = config_subparsers.add_parser("get")
    config_get.add_argument("key")

    config_delete = config_subparsers.add_parser("delete")
    config_delete.add_argument("key")

    config_subparsers.add_parser("prune")
    config_subparsers.add_parser("show")

    task_parser = subparsers.add_parser("task")
    task_subparsers = task_parser.add_subparsers(
        dest="task_command",
        required=True,
    )

    task_goal = task_subparsers.add_parser("goal")
    task_goal.add_argument("task_id")

    task_fqns = task_subparsers.add_parser("FullQualifiedNames")
    task_fqns.add_argument("task_id")
    task_fqns.add_argument("--goal", required=True)

    task_interfaces = task_subparsers.add_parser("interfaces")
    task_interfaces.add_argument("task_id")
    task_interfaces.add_argument("--goal", required=True)
    task_interfaces.add_argument("--FullQualifiedNames", required=True)

    task_sequence = task_subparsers.add_parser("sequence")
    task_sequence.add_argument("task_id")
    task_sequence.add_argument("--goal", required=True)
    task_sequence.add_argument("--FullQualifiedNames", required=True)
    task_sequence.add_argument("--interfaces", required=True)

    task_gherkins = task_subparsers.add_parser("gherkins")
    task_gherkins.add_argument("task_id")
    task_gherkins.add_argument("--goal", required=True)
    task_gherkins.add_argument("--FullQualifiedNames", required=True)
    task_gherkins.add_argument("--interfaces", required=True)
    task_gherkins.add_argument("--sequence", required=True)

    task_run = task_subparsers.add_parser("run")
    task_run.add_argument("task_id")

    workflow_parser = subparsers.add_parser("workflow")
    workflow_subparsers = workflow_parser.add_subparsers(
        dest="workflow_command",
        required=True,
    )

    workflow_run = workflow_subparsers.add_parser("run")
    workflow_run.add_argument("workflow_id")

    run_parser = subparsers.add_parser("run")
    run_subparsers = run_parser.add_subparsers(
        dest="run_command",
        required=True,
    )

    agent_parser = run_subparsers.add_parser("agent")
    agent_subparsers = agent_parser.add_subparsers(
        dest="agent",
        required=True,
    )

    for agent in (
        "researcher",
        "implementer",
        "tester",
        "fixer",
    ):
        agent_subparsers.add_parser(agent)

    return parser


def dispatch(
    args: argparse.Namespace,
    *,
    reader: StdinReader,
    writer: StdoutWriter,
) -> object:
    root = args.root

    if args.command == "info":
        return run_info_command()

    if args.command == "init":
        return run_init_command(root)

    if args.command == "validate":
        return validate_project(root)

    if args.command == "config":
        if args.config_command == "set":
            return run_config_set_command(
                root=root,
                key=args.key,
                value=args.value,
            )

        if args.config_command == "get":
            return run_config_get_command(
                root=root,
                key=args.key,
            )

        if args.config_command == "delete":
            return run_config_delete_command(
                root=root,
                key=args.key,
            )

        if args.config_command == "prune":
            return run_config_prune_command(root=root)

        if args.config_command == "show":
            return run_config_show_command(root=root)

    if args.command == "task":
        if args.task_command == "goal":
            return run_create_goal_command(
                root=root,
                task_id=args.task_id,
            )

        if args.task_command == "FullQualifiedNames":
            return run_create_fqns_command(
                root=root,
                task_id=args.task_id,
                goal=args.goal,
            )

        if args.task_command == "interfaces":
            return run_create_interfaces_command(
                root=root,
                task_id=args.task_id,
                goal=args.goal,
                FullQualifiedNames=args.fqns,
            )

        if args.task_command == "sequence":
            return run_create_sequence_command(
                root=root,
                task_id=args.task_id,
                goal=args.goal,
                FullQualifiedNames=args.fqns,
                interfaces=args.interfaces,
            )

        if args.task_command == "gherkins":
            return run_create_gherkins_command(
                root=root,
                task_id=args.task_id,
                goal=args.goal,
                FullQualifiedNames=args.fqns,
                interfaces=args.interfaces,
                sequence=args.sequence,
            )

        if args.task_command == "run":
            return run_task_command(
                root=root,
                task_id=args.task_id,
            )

    if args.command == "workflow":
        if args.workflow_command == "run":
            return run_workflow_command(
                root=root,
                workflow_id=args.workflow_id,
            )

    if args.command == "run" and args.run_command == "agent":
        data = reader.read()
        data["root"] = root
        data = prepare_agent_input(args.agent, data)

        commands: dict[str, Callable[..., object]] = {
            "researcher": run_agent_researcher_command,
            "implementer": run_agent_implementer_command,
            "tester": run_agent_tester_command,
            "fixer": run_agent_fixer_command,
        }

        return commands[args.agent](**data)

    raise InvalidRequestError("Неизвестная команда")


def main(argv: list[str] | None = None) -> int:
    global termination_signal

    termination_signal = signal.SIGINT

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    reader = StdinReader()
    writer = StdoutWriter()

    try:
        parser = build_parser()
        args = parser.parse_args(argv)

        result = dispatch(
            args,
            reader=reader,
            writer=writer,
        )

        writer.success(result)

        if args.command == "validate" and isinstance(result, dict) and not result["valid"]:
            return 1

        return 0

    except CLIArgumentError as error:
        writer.failure(
            error_type="CLIArgumentError",
            message=str(error),
            code="INVALID_ARGUMENTS",
        )
        return 2

    except InvalidRequestError as error:
        writer.failure(
            error_type="InvalidRequestError",
            message=str(error),
            code="INVALID_REQUEST",
        )
        return 2

    except KeyboardInterrupt:
        writer.failure(
            error_type="KeyboardInterrupt",
            message="Выполнение прервано",
            code="INTERRUPTED",
        )
        return 130 if termination_signal == signal.SIGINT else 143

    except Exception as error:
        writer.failure(
            error_type=type(error).__name__,
            message=str(error),
            code="COMMAND_EXECUTION_ERROR",
        )
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
