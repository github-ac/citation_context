#!/bin/bash
set -e

source config.sh

docker_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
main_dir="${docker_dir}/.."

docker stop $container_name || true
docker rm $container_name || true
docker run -td \
           --name $container_name \
           --restart=unless-stopped \
           -v $main_dir:$mount_dir \
           -d $image_name
