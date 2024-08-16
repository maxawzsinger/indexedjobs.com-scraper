#!/bin/bash

# This script is for development purposes, allows you to quickly update a Lambda function
# bash updateDocker.sh -r <region> -n <repository_name> -u <ECR_URL> -f <lambda_function_name>

# Example of calling the script with dummy parameters:
# bash updateDocker.sh -r us-west-1 -n myappimages -u 123456789012.dkr.ecr.us-west-1.amazonaws.com/myappimages -f my_lambda_function

# Parse CLI arguments for sensitive data
while getopts r:n:u:f: flag
do
    case "${flag}" in
        r) AWS_REGION=${OPTARG};;
        n) REPOSITORY_NAME=${OPTARG};;
        u) ECR_URI=${OPTARG};;
        f) LAMBDA_FUNCTION_NAME=${OPTARG};;
    esac
done

# Validate the inputs
if [[ -z "$AWS_REGION" || -z "$REPOSITORY_NAME" || -z "$ECR_URI" || -z "$LAMBDA_FUNCTION_NAME" ]]; then
    echo "Usage: $0 -r <AWS_REGION> -n <REPOSITORY_NAME> -u <ECR_URI> -f <LAMBDA_FUNCTION_NAME>"
    exit 1
fi

# Step 1: Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI > /dev/null 2>&1

# Step 2: Delete All Images in ECR Repository
aws ecr batch-delete-image --region $AWS_REGION \
    --repository-name $REPOSITORY_NAME \
    --image-ids "$(aws ecr list-images --region $AWS_REGION --repository-name $REPOSITORY_NAME --query 'imageIds[*]' --output json)" > /dev/null 2>&1 || true

# Step 3: Build Docker Image
docker build --platform linux/amd64 -t docker-image:test .

# Step 4: Tag Docker Image
docker tag docker-image:test $ECR_URI:latest

# Step 5: Push Docker Image
docker push $ECR_URI:latest

# Step 6: Update Lambda Function Code
aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --image-uri $ECR_URI:latest > /dev/null 2>&1
