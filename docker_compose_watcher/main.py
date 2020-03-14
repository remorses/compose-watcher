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
from compose.cli.main import dispatch
from threading import Thread


def restart(file, service_name):
    try:
        logger.debug(f"restarting {service_name}")
        sys.argv = ["docker-compose", "--file", file, "restart", service_name]
        command = dispatch()
        command()
        logger.debug("finish restarting")
    except Exception as e:
        return
    except SystemExit as e:
        return
    except BaseException as e:
        return


class Handler(FileSystemEventHandler):
    service: ServiceToWatch
    file: str

    def __init__(self, service, file):
        super().__init__()
        self.service = service
        self.file = file

    def on_any_event(self, event: FileSystemEvent):
        super().on_any_event(event)
        logger.debug("change")
        src = event.src_path
        # thread = Thread(target=restart, kwargs=dict(file=self.file, service_name=self.service.name))
        # thread.start()
        restart(file=self.file, service_name=self.service.name)

        # for parent_path in self.service.volumes:
        #     if path_is_parent(parent_path, src):
        #         logger.info(f"for {src}, child of volume {parent_path}")


def get_volumes_paths(service: dict):
    f = service.get("volumes")
    if isinstance(f, list):
        for vol in f:
            if isinstance(vol, str):
                path, _, _ = vol.partition(":")
                if path:
                    yield path
            if isinstance(vol, dict):
                if vol.get("source"):
                    yield vol.get("source")
    if isinstance(f, dict):
        for _, path in f.items():
            yield path
    return []


def get_cli_input(compose: dict, file: str) -> CliInput:
    input = CliInput(services=[], file=file)

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
    logger.debug(f"file {file}")
    data = load_file(file)
    compose = yaml.safe_load(data)
    input = get_cli_input(compose, file)
    logger.debug(f"input {input}")
    watch(input)


def watch(input: CliInput):
    observer = Observer()
    for service in input.services:
        event_handler = Handler(service=service, file=input.file)
        for path in service.volumes:
            print(f"watching `{path}` for service `{service.name}`")
            observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()




