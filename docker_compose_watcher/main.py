import sys
import os.path
import yaml
import time
import logging
from .logger import logger
from .support import load_file, path_is_parent
from compose.cli.main import perform_command, TopLevelCommand
from compose.cli.command import project_from_options
from .constants import DOCKER_COMPOSE_NAMES
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileSystemEvent
from docker_compose_watcher.types import CliInput, ServiceToWatch


class Handler(FileSystemEventHandler):
    service: ServiceToWatch

    def restart(self,):
        logger.debug('restarting')
        command = TopLevelCommand(self.project)
        command.run({"COMMAND": "restart", "SERVICE": self.service.name})
        pass

    def __init__(self, service, ):
        super().__init__()
        self.service = service

    def on_any_event(self, event: FileSystemEvent):
        super().on_any_event(event)
        logger.debug('change')
        src = event.src_path
        self.restart()

        # for parent_path in self.service.volumes:
        #     if path_is_parent(parent_path, src):
        #         logger.info(f"for {src}, child of volume {parent_path}")


def get_volumes_paths(service: dict):
    f = service.get("volumes")
    if isinstance(f, list):
        for vol in f:
            if isinstance(vol, str):
                _, _, path = vol.partition("=")
                if path:
                    yield path
            if isinstance(vol, dict):
                if vol.get("source"):
                    yield vol.get("source")
    if isinstance(f, dict):
        for _, path in f.items():
            yield path
    return []


def get_cli_input(compose: dict, options: dict) -> CliInput:
    input = CliInput(services=[], )

    for service_name, service in compose.get("services", {}).items():
        if not service:
            continue
        volumes = list(get_volumes_paths(service))
        extensions = []
        input.services.append(
            ServiceToWatch(name=service_name, volumes=volumes, extensions=extensions)
        )
        # TODO add extensions from labels
    return input


def main(file=None):
    if not file:
        for name in DOCKER_COMPOSE_NAMES:
            if os.path.exists(name):
                file = name
    logger.debug(f'file {file}')
    data = load_file(file)
    compose = yaml.safe_load(data)
    input = get_cli_input(compose, {"--file": file})
    watch(input)


def watch(input: CliInput):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    observer = Observer()
    for service in input.services:
        event_handler = Handler(service=service,)
        for path in service.volumes:
            observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

