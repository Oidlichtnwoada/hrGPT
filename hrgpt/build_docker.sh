#!/bin/sh

# terminate on first error
set -e

# build the Dockerfile
docker build .. -f ./Dockerfile
