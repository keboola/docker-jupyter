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


# Push to ACR
AZURE_REGISTRY_NAME='keboola'
AZURE_REPOSITORY='keboola.azurecr.io/sandbox-jupyter'
AZURE_RESOURCE_GROUP='keboola-acr-prod-rg'
AZURE_SERVICE_PRINCIPAL_TENANT='9b85ee6f-4fb0-4a46-8cb7-4dcc6b262a89'
docker tag $IMAGE_NAME:latest $AZURE_REPOSITORY:$TRAVIS_TAG
docker tag $IMAGE_NAME:latest $AZURE_REPOSITORY:latest

docker run --volume /var/run/docker.sock:/var/run/docker.sock quay.io/keboola/azure-cli sh -c "az login --service-principal -u $AZURE_SERVICE_PRINCIPAL -p $AZURE_SERVICE_PRINCIPAL_PASSWORD --tenant $AZURE_SERVICE_PRINCIPAL_TENANT && az acr login --resource-group $AZURE_RESOURCE_GROUP --name $AZURE_REGISTRY_NAME && docker push $AZURE_REPOSITORY:latest && docker push $AZURE_REPOSITORY:$TRAVIS_TAG"
