#!/usr/bin/env python3
"""本地 Claude Agent CLI。

示例:
  python -m agents.cli run rag-bot --mode live --query "发票怎么开"
  python -m agents.cli run content-bot --mode live --task "618 大促海报" --template longform
  python -m agents.cli cost content-bot
  python -m agents.cli cost content-bot --reset
"""
from __future__ import annotations

import argparse
import json
import sys

from agents.coagent_client import CoAgentClient
from agents.registry import AGENT_IDS, get_agent


def _print(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_run(args: argparse.Namespace) -> int:
    client = CoAgentClient()
    if not client.health():
        print("CoAgent 未运行，请先: uvicorn app.main:app --port 8000", file=sys.stderr)
        return 1

    agent = get_agent(args.agent_id)
    if args.mode == "simulate":
        _print(agent.run_simulate())
        return 0

    if args.agent_id == "content-bot":
        _print(agent.run_live(args.task or "营销长文案", template=args.template))
    elif args.agent_id == "rag-bot":
        if not args.query:
            print("rag-bot live 模式需要 --query", file=sys.stderr)
            return 2
        _print(agent.run_live(args.query))
    else:
        if not args.query:
            print("cs-bot live 模式需要 --query", file=sys.stderr)
            return 2
        _print(agent.run_live(args.query))
    return 0


def cmd_retry(args: argparse.Namespace) -> int:
    if args.agent_id != "cs-bot":
        print("当前仅 cs-bot 支持 retry", file=sys.stderr)
        return 2
    agent = get_agent("cs-bot")
    _print(agent.retry())
    return 0


def cmd_cost(args: argparse.Namespace) -> int:
    if args.agent_id != "content-bot":
        print("当前仅 content-bot 支持 cost", file=sys.stderr)
        return 2
    agent = get_agent("content-bot")
    if args.reset:
        _print(agent.reset_cost())
    else:
        _print(agent.get_cost_status())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CoAgent 本地 Claude Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="运行 Agent")
    run_p.add_argument("agent_id", choices=AGENT_IDS)
    run_p.add_argument("--mode", choices=("live", "simulate"), default="simulate")
    run_p.add_argument("--query", help="用户问题（cs-bot / rag-bot live）")
    run_p.add_argument("--task", help="内容 brief（content-bot live）")
    run_p.add_argument(
        "--template",
        choices=("standard", "longform", "batch"),
        default="longform",
        help="content-bot 模板：standard / longform(默认) / batch",
    )
    run_p.set_defaults(func=cmd_run)

    retry_p = sub.add_parser("retry", help="cs-bot 重试")
    retry_p.add_argument("agent_id", choices=("cs-bot",))
    retry_p.set_defaults(func=cmd_retry)

    cost_p = sub.add_parser("cost", help="content-bot 日累计成本")
    cost_p.add_argument("agent_id", choices=("content-bot",))
    cost_p.add_argument("--reset", action="store_true", help="重置今日累计")
    cost_p.set_defaults(func=cmd_cost)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
