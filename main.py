"""PandorickKi platform entry point."""

from __future__ import annotations

import asyncio
from argparse import ArgumentParser
from contextlib import suppress

from config import PlatformConfig
from orchestrator import Orchestrator
from web.api import WebControlServer


def main() -> None:
    """Start the PandorickKi integration platform."""

    parser = ArgumentParser(description="PandorickKi integration platform")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        action="store_true",
        help="run one orchestration cycle and exit",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="run continuously with live ControlCenter terminal view",
    )
    mode.add_argument(
        "--headless",
        action="store_true",
        help="run continuously without terminal live view",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="seconds between continuous cycles",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=None,
        help="seconds between live ControlCenter redraws",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="optional maximum cycles for tests or controlled runs",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="start the local web ControlCenter on 127.0.0.1",
    )
    parser.add_argument(
        "--web-host",
        default="127.0.0.1",
        help="local web ControlCenter host",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8000,
        help="local web ControlCenter port",
    )
    control = parser.add_mutually_exclusive_group()
    control.add_argument(
        "--control-on",
        action="store_true",
        help="enable ControlCenter for this run",
    )
    control.add_argument(
        "--control-off",
        action="store_true",
        help="disable ControlCenter for this run",
    )
    args = parser.parse_args()
    config = PlatformConfig.from_env()
    if args.control_on:
        config = config.with_control_center(True)
    elif args.control_off:
        config = config.with_control_center(False)
    warnings = config.validate()

    print("PandorickKi Grundsystem gestartet.")
    for warning in warnings:
        print(f"Config warning: {warning}")

    interval = args.interval if args.interval is not None else config.cycle_interval
    refresh = args.refresh if args.refresh is not None else config.control_refresh_seconds

    live_requested = args.live and config.control_center_enabled
    if args.live and not config.control_center_enabled:
        print("ControlCenter ist ausgeschaltet; Live-Anzeige wird als Headless gestartet.")

    if args.live:
        report = asyncio.run(
            run_platform_continuous(
                live=live_requested,
                interval=interval,
                refresh=refresh,
                cycles=args.cycles,
                config=config,
                web=args.web,
                web_host=args.web_host,
                web_port=args.web_port,
            )
        )
    elif args.headless:
        report = asyncio.run(
            run_platform_continuous(
                live=False,
                interval=interval,
                refresh=refresh,
                cycles=args.cycles,
                config=config,
                web=args.web,
                web_host=args.web_host,
                web_port=args.web_port,
            )
        )
    else:
        report = asyncio.run(run_platform_once(config=config))

    print(f"Health: {report.status}")
    print(f"Services: {', '.join(f'{name}={status}' for name, status in report.services.items())}")
    if args.live:
        print("Modus: live" if live_requested else "Modus: live-control-off")
    elif args.headless:
        print("Modus: headless")
    else:
        print("Modus: single cycle")
    if args.web:
        print(f"Web ControlCenter: http://{args.web_host}:{args.web_port}")


async def run_platform_once(config: PlatformConfig | None = None):
    """Run one safe platform cycle."""

    orchestrator = Orchestrator(config=config)
    await orchestrator.start()
    try:
        return await orchestrator.run_once()
    finally:
        await orchestrator.stop()


async def run_platform_continuous(
    *,
    live: bool,
    interval: float,
    refresh: float,
    cycles: int | None,
    config: PlatformConfig | None = None,
    web: bool = False,
    web_host: str = "127.0.0.1",
    web_port: int = 8000,
):
    """Run the platform continuously until Ctrl+C or max cycles."""

    orchestrator = Orchestrator(config=config)
    web_server: WebControlServer | None = None
    await orchestrator.start()
    try:
        if web:
            web_server = WebControlServer(
                orchestrator,
                host=web_host,
                port=web_port,
                warm_learning_report=cycles is None,
            )
            web_server.start()
            print(f"PandorickKi Web ControlCenter gestartet: {web_server.url}")
        return await orchestrator.run_continuous(
            cycle_interval=interval,
            live_control=live,
            refresh_seconds=refresh,
            final_control_snapshot=False,
            max_cycles=cycles,
            should_pause=web_server.is_paused if web_server else None,
            should_stop=web_server.should_stop if web_server else None,
            take_restart_request=web_server.take_restart_request if web_server else None,
        )
    except KeyboardInterrupt:
        with suppress(Exception):
            return await orchestrator.run_once(final_control_snapshot=not live)
        raise
    finally:
        if web_server is not None:
            web_server.stop()
        await orchestrator.stop()


if __name__ == "__main__":
    main()
