#!/bin/sh

# terminate on first error
set -e

# build the Dockerfile
docker build --platform linux/amd64,linux/arm64build .. -f ./Dockerfile -t hrgpt:latest
