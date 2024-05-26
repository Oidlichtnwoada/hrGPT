#!/bin/sh

# terminate on first error
set -e

# build the image
./build_docker.sh

# get the current project id
PROJECT_ID=$(gcloud config get-value project)

# tag the built image
docker tag hrgpt:latest gcr.io/$PROJECT_ID/hrgpt:latest

# configure credentials
gcloud auth configure-docker

# push the image to gcr
docker push gcr.io/$PROJECT_ID/hrgpt:latest

# deploy the image
gcloud run deploy hrgpt --image gcr.io/$PROJECT_ID/hrgpt:latest --platform managed --region europe-west3 --allow-unauthenticated --port 80
