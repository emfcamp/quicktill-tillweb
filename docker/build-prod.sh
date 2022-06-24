#!/bin/bash

# Run with the project root as the current working directory

set -e

docker build -t emftillweb-postgres docker/data
docker build -t emftillweb-app -f Dockerfile.prod .
docker build -t emftillweb-static docker/static
