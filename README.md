# compose-watcher

<p align="center">
    <img src='https://raw.githubusercontent.com/remorses/compose-watcher/master/.github/compose_watcher_video.gif'>
</p>

Cli that restarts you docker compose services when a file inside one of its volumes changes
To use with compiled languages place the compilation step in the `command` field.

Example usage

-   graphql api restart when schema file changes
-   [Mongoke](https://github.com/remorses/mongoke) restarts when config schema changes
-   Nodejs container restarts when the src folder changes, recompiling with tsc

## Install

```
pip3 install compose-watcher
```

## Usage

Use the directories you want to track as service volumes
Also consider using `init: true` in the compose service definition for faster killing of processes.
To not stop the `docker-compose logs` command, there should be always a running container

```
version: '3'

services:
  api:
    build: node_api
    command: sh -c 'tsc --incremental && node index.js'
    volumes:
      - ./node_api/src:/src

```

Then execute `compose-watcher` to watch changes

```
compose-watcher -f docker-compose.yml --timeout 5
```

TODO add extension filter
TODO add services names as positional arguments
TODO dont block the event receiving thread when restarting

