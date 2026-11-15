from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from config import make_config
from factories import make_task, make_task_runner, make_workflow, make_workflow_runner
from models import TaskStatus


def _cmd_info(_: argparse.Namespace) -> int:
    header: tuple[str, str, str, str] = (
        "№",
        "Command",
        "Description",
        "Example",
    )
    rows: list[tuple[str, str, str, str]] = [
        (
            "1",
            "config set <key> <value>",
            "Set a config value",
            "config set max_fix_attempts 5",
        ),
        (
            "2",
            "config get <key>",
            "Show a config value",
            "config get max_fix_attempts",
        ),
        (
            "3",
            "config delete <key>",
            "Delete a config key",
            "config delete max_fix_attempts",
        ),
        ("4", "config clear", "Remove the config file", "config clear"),
        ("5", "info", "Show this table", "info"),
        ("6", "init", "Scaffold the workspace", "init"),
        (
            "7",
            "run task <id>",
            "Run a single task",
            "run task 001_products_repository",
        ),
        (
            "8",
            "run workflow <id>",
            "Run a whole workflow",
            "run workflow end_to_end",
        ),
    ]

    widths = [max(len(row[i]) for row in [*rows, header]) for i in range(4)]
    lines: list[str] = [
        "  ".join(f"{h:<{w}}" for h, w in zip(header, widths, strict=True)),
        "  ".join("-" * w for w in widths),
    ]
    for row in rows:
        lines.append("  ".join(f"{c:<{w}}" for c, w in zip(row, widths, strict=True)))

    print("\n".join(lines))
    return 0


def _cmd_init(_: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    files: tuple[str, ...] = ("AGENT.md", "AGENT.yaml")
    dirs: tuple[str, ...] = ("skills", "tasks", "workflows")

    for name in files:
        path = root / name
        if path.exists():
            print(f"exists: {path}")
        else:
            path.touch()
            print(f"created: {path}")

    for name in dirs:
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        print(f"ready: {directory}")

    return 0


def _cmd_config_set(args: argparse.Namespace) -> int:
    target_path = Path.cwd().resolve() / "AGENT.yaml"
    data = {}
    if target_path.exists():
        with target_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    data[args.key] = args.value
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )

    print(f"{args.key} = {args.value}")
    return 0


def _cmd_config_get(args: argparse.Namespace) -> int:
    target_path = Path.cwd().resolve() / "AGENT.yaml"
    data = {}
    if target_path.exists():
        with target_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    print(data.get(args.key))
    return 0


def _cmd_config_delete(args: argparse.Namespace) -> int:
    target_path = Path.cwd().resolve() / "AGENT.yaml"
    data = {}
    if target_path.exists():
        with target_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    data.pop(args.key, None)
    target_path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )

    print(f"{args.key}: deleted")
    return 0


def _cmd_config_clear(_: argparse.Namespace) -> int:
    target = Path.cwd().resolve() / "AGENT.yaml"
    if target.exists():
        target.unlink()
        print(f"cleared: {target}")
    else:
        print(f"nothing to clear: {target}")

    return 0


def _cmd_run_task(args: argparse.Namespace) -> int:
    config = make_config(Path.cwd())
    task = make_task(config, args.task_id)
    task_runner = make_task_runner(config)

    result = task_runner.run(task)

    print(f"task {result.task_id}: {result.status}")
    return 0 if result.status is TaskStatus.SUCCESS else 1


def _cmd_run_workflow(args: argparse.Namespace) -> int:
    config = make_config(Path.cwd())
    workflow = make_workflow(config, args.workflow_id)
    workflow_runner = make_workflow_runner(config)

    result = workflow_runner.run(workflow)

    success = sum(1 for r in result.results if r.status is TaskStatus.SUCCESS)
    total = len(result.results)
    error = total - success

    for task_result in result.results:
        print(f"task {task_result.task_id}: {task_result.status}")

    print(f"workflow {args.workflow_id}: {success}/{total} done, {error} failed")
    return 0 if (total and success == total) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info
    info_parser = subparsers.add_parser("info", help="Show agent info.")
    info_parser.set_defaults(func=_cmd_info)

    # init
    init_parser = subparsers.add_parser("init", help="Initialize workspace.")
    init_parser.set_defaults(func=_cmd_init)

    # config
    config_parser = subparsers.add_parser("config", help="Manage config.")
    config_sub = config_parser.add_subparsers(dest="config_command", required=True)

    config_set_parser = config_sub.add_parser("set", help="Set config key.")
    config_set_parser.add_argument("key", type=str)
    config_set_parser.add_argument("value", type=str)
    config_set_parser.set_defaults(func=_cmd_config_set)

    config_get_parser = config_sub.add_parser("get", help="Get config key.")
    config_get_parser.add_argument("key", type=str)
    config_get_parser.set_defaults(func=_cmd_config_get)

    config_delete_parser = config_sub.add_parser("delete", help="Delete config key.")
    config_delete_parser.add_argument("key", type=str)
    config_delete_parser.set_defaults(func=_cmd_config_delete)

    config_clear_parser = config_sub.add_parser("clear", help="Clear config.")
    config_clear_parser.set_defaults(func=_cmd_config_clear)

    # run
    run_parser = subparsers.add_parser("run", help="Run a task or workflow.")
    run_sub = run_parser.add_subparsers(dest="run_command", required=True)

    run_task_parser = run_sub.add_parser("task", help="Run a single task.")
    run_task_parser.add_argument("task_id", type=str)
    run_task_parser.set_defaults(func=_cmd_run_task)

    run_workflow_parser = run_sub.add_parser("workflow", help="Run a workflow.")
    run_workflow_parser.add_argument("workflow_id", type=str)
    run_workflow_parser.set_defaults(func=_cmd_run_workflow)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None and len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
