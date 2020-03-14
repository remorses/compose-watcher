import pytest
from docker_compose_watcher.main import watch, CliInput, ServiceToWatch, get_cli_input
from docker_compose_watcher.support import path_is_parent
 

def test_get_cli_input():
    compose = {
        "services": {
            "x": {"volumes": ["a:patha", "b:pathb"]},
            "y": {"volumes": {"a": "patha", "b": "pathb"}},
        }
    }
    input = get_cli_input(compose, 'docker_compose.yml')
    print(input)
    assert input

@pytest.mark.skip
def test_watch():
    watch(CliInput(services=[ServiceToWatch("x", volumes=["."])]))


def test_ready():
    assert True

def test_path_is_parent():
    x = path_is_parent('/a/b', '/a/b/c')
    assert x
    x = path_is_parent('/a/b', '/a/b/c/')
    assert x
    x = path_is_parent('/a/b/c', '/a/b/c')
    assert x
    x = path_is_parent('/a/b/c', '/a/b')
    assert not x


if __name__ == "__main__":
    test_watch()
