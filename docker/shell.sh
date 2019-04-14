#!/bin/bash
set -e

source config.sh

docker exec -it $container_name /bin/bash
