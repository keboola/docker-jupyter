#!/bin/bash

docker login -e="." -u="$QUAY_USERNAME" -p="$QUAY_PASSWORD" quay.io
docker tag keboola/docker-jupyter quay.io/keboola/docker-jupyter:$TRAVIS_TAG
docker tag keboola/docker-jupyter quay.io/keboola/docker-jupyter:latest
docker images
docker push quay.io/keboola/docker-jupyter:$TRAVIS_TAG
docker push quay.io/keboola/docker-jupyter:latest
