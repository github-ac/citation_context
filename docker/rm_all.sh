#!/bin/bash
set -e

source config.sh

docker stop $container_name
docker rm $container_name
docker rmi $image_name
