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

global_timeout = 3


def main(service_names=[], file=None, timeout=3):
    global global_timeout
    global_timeout = timeout
    if not file:
        for name in DOCKER_COMPOSE_NAMES:
            if os.path.exists(name):
                file = name
    print(f"reading volumes paths from {file}")
    logger.debug(f"file {file}")
    data = load_file(file)
    compose = yaml.safe_load(data)
    input = get_cli_input(compose, file=file, service_names=service_names)
    logger.debug(f"input {input}")
    watch(input)


def watch(input: CliInput):
    observer = Observer()
    for service in input.services:
        for path in service.volumes:
            print(f"watching `{path}` for service `{service.name}`")
            is_dir = os.path.isdir(path)
            single_path = None
            if not is_dir:
                single_path = os.path.basename(path)
                path = os.path.dirname(os.path.abspath(path))
            handler = Handler(service=service, file=input.file, single_path=single_path)
            observer.schedule(handler, path, recursive=is_dir)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class Handler(FileSystemEventHandler):
    service: ServiceToWatch
    file: str

    def __init__(self, service, file, single_path=None):
        super().__init__()
        self.service = service
        self.file = file
        self.single_path = single_path

    def on_any_event(self, event: FileSystemEvent):
        super().on_any_event(event)
        src = os.path.basename(os.path.abspath(event.src_path))
        logger.debug("change")
        logger.debug(f"event.src={src}")
        logger.debug(f"single_path={self.single_path}")
        if self.single_path and os.path.normpath(src) != os.path.normpath(
            self.single_path
        ):
            return
        thread = Thread(
            target=restart, kwargs=dict(file=self.file, service_name=self.service.name)
        )
        thread.start()
        thread.join()
        for dep in self.service.dependents:
            thread = Thread(
                target=restart,
                kwargs=dict(file=self.file, service_name=dep, skip_dependencies=True),
            )
            thread.start()
            thread.join()

        # TODO use a thread to not stop the ingestion of events, the thread discards events if a restart is already happening
        # restart(file=self.file, service_name=self.service.name)

        # for parent_path in self.service.volumes:
        #     if path_is_parent(parent_path, src):
        #         logger.info(f"for {src}, child of volume {parent_path}")


def restart(file, service_name, skip_dependencies=False):
    global global_timeout
    try:
        logger.debug(f"restarting {service_name}")
        common = ["docker-compose", "--log-level", "ERROR", "--file", file]
        if skip_dependencies:
            sys.argv = [*common, "restart", "-t", str(global_timeout), service_name]
        else:
            sys.argv = [
                *common,
                "up",
                "--force-recreate",
                "-d",
                "-t",
                str(global_timeout),
                service_name,
            ]
        command = dispatch()
        command()
        logger.debug("finish restarting")
    except Exception as e:
        print(e)
        return
    except SystemExit as e:
        return
    except BaseException as e:
        print(e)
        return


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


def get_cli_input(compose: dict, file: str, service_names=[]) -> CliInput:
    input = CliInput(services=[], file=file)
    services = compose.get("services", {}).items()
    for service_name, service in services:
        if not service:
            continue
        if service_names and service_name not in service_names:
            continue
        volumes = list(get_volumes_paths(service))
        extensions = []
        input.services.append(
            ServiceToWatch(
                name=service_name, volumes=volumes, extensions=extensions, dependents=[]
            )
        )
        # TODO add extensions from labels

    # add dependents
    for service_name, service in services:
        depends_on = service.get("depends_on", [])
        if not depends_on:
            continue
        if isinstance(depends_on, str):
            depends_on = [depends_on]
        for dep in depends_on:
            for x in input.services:
                if x.name == dep:
                    x.dependents.append(service_name)

    return input

