#!/bin/bash
set -e

IMAGE_NAME='keboola/docker-jupyter'

# Push to Quay.io
docker login -u="$QUAY_USERNAME" -p="$QUAY_PASSWORD" quay.io
docker tag $IMAGE_NAME quay.io/$IMAGE_NAME:${TRAVIS_TAG}
docker tag $IMAGE_NAME quay.io/$IMAGE_NAME:latest
docker images
docker push quay.io/$IMAGE_NAME:${TRAVIS_TAG}
docker push quay.io/$IMAGE_NAME:latest


# Push to ECR
ECR_REPOSITORY='147946154733.dkr.ecr.us-east-1.amazonaws.com'
# install aws cli w/o sudo
pip install --user awscli
# put aws in the path
export PATH=$PATH:$HOME/.local/bin
# needs AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY envvars
eval $(aws ecr get-login --region us-east-1 --no-include-email)
docker tag $IMAGE_NAME:latest $ECR_REPOSITORY/$IMAGE_NAME:$TRAVIS_TAG
docker tag $IMAGE_NAME:latest $ECR_REPOSITORY/$IMAGE_NAME:latest
docker push $ECR_REPOSITORY/$IMAGE_NAME:$TRAVIS_TAG
docker push $ECR_REPOSITORY/$IMAGE_NAME:latest

