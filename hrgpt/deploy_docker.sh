#!/bin/sh

# terminate on first error
set -e

# build the image
./build_docker.sh

# deploy the image
gcloud run deploy hrgpt --image hrgpt:latest --platform managed --region europe-west3 --allow-unauthenticated --port 80
