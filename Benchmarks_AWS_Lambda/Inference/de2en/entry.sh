#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec /usr/bin/aws-lambda-rie /app/env/bin/python3.8 -m awslambdaric $1
else
    exec /app/env/bin/python3.8 -m awslambdaric $1
fi