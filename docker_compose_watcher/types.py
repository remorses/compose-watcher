from dataclasses import dataclass
from typing import List
from compose.project import Project


@dataclass
class ServiceToWatch:
    name: str
    volumes: List[str]
    extensions: List[str]


@dataclass
class CliInput:
    file: str
    services: List[ServiceToWatch]
