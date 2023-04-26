#!/bin/bash

# First, create a bucket on S3 to use as the host for the deployment packages
# This script takes that bucket name as the first input 
# Second, create an execution role in AWS console. The execution role needs Full Lambda Access permissions
# This script takes that execution role ARN as the second input
# Finally, include the AWS account number as the third parameter
#
# Example: ./deploy_classify.sh <S3-Bucket-Name> <Execution-Role-ARN> <AWS-Account-ID>
export AWS_PAGER=""

model=$1

cp params.py ${model}/app/

func_name=${model}

cd ${model}/

docker build -t ${model}-img .

cd ../

pwd=$(aws ecr get-login-password --region us-west-2)

aws ecr delete-repository --repository-name ${model}-img

aws ecr create-repository --repository-name ${model}-img

docker login -u AWS -p $pwd $3.dkr.ecr.us-west-2.amazonaws.com

docker tag ${model}-img:latest $3.dkr.ecr.us-west-2.amazonaws.com/${model}-img:latest

docker push $3.dkr.ecr.us-west-2.amazonaws.com/${model}-img:latest

aws lambda create-function --function-name $func_name --role $2 --code "ImageUri=$3.dkr.ecr.us-west-2.amazonaws.com/${model}-img:latest" --package-type "Image"

echo "Sleeping for 60 seconds before updating the function's memory size and timeout"

sleep 60

if [ $func_name = "langdetect" ]
then
    aws lambda update-function-configuration --function-name  $func_name --memory-size 4000 --timeout 240 --ephemeral-storage 2048
else
    aws lambda update-function-configuration --function-name  $func_name --memory-size 2048 --timeout 180
fi