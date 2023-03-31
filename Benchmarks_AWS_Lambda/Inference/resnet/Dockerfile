# Define global args
ARG FUNCTION_DIR="./app/"
ARG VENV_PATH="/app/env"
ARG JAVA_RUNTIME_VERSION="20"
ARG DISTRO_VERSION="3.16"

### 1. Get base jdk
FROM amazoncorretto:${JAVA_RUNTIME_VERSION}-al2-jdk AS base_runtime

RUN amazon-linux-extras enable python3.8
RUN yum install -y python38 python38-devel openssl-devel && yum install -y libcurl-devel

# # Install python
ENV PYTHONUNBUFFERED=1
RUN python3.8 -m ensurepip
RUN pip3.8 install --no-cache --upgrade pip setuptools

ARG VENV_PATH
# Create and activate venv
ENV VIRTUAL_ENV=${VENV_PATH}
RUN python3.8 -m venv ${VIRTUAL_ENV}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV LOG_LOCATION="/tmp/tslogs"
ENV METRICS_LOCATION="/tmp/tslogs"

# # Install deps using a build image
FROM base_runtime AS build-image

RUN yum install -y \
    build-base \
    libtool \
    autoconf \
    automake \
    libexecinfo-dev \
    make \
    cmake

# Optional – Install the function's dependencies
ENV PYCURL_SSL_LIBRARY=openssl
RUN pip install --no-cache wheel && pip install --no-cache torch torchvision --index-url https://download.pytorch.org/whl/cpu \
 --extra-index-url https://pypi.org/simple \
 boto3 pyyaml captum torchserve torch-model-archiver torch-workflow-archiver pycurl certifi \
 awslambdaric

ARG FUNCTION_DIR

# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Copy handler function
COPY app/* ${FUNCTION_DIR}
# Final lambda image
FROM base_runtime AS final-image
# #ENV JAVA_HOME="/usr/lib/jvm/java-1.8-openjdk"

# EXPOSE 81    
# ADD test.py /
# CMD ["python", "test.py"]

# Include global arg in this stage of the build
ARG FUNCTION_DIR

RUN mkdir -p /tmp/tslogs
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}
# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ./
# (Optional) Add Lambda Runtime Interface Emulator and use a script in the ENTRYPOINT for simpler local runs
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
COPY entry.sh /
RUN chmod 755 /usr/bin/aws-lambda-rie /entry.sh
EXPOSE 10000 10001 10002
ENTRYPOINT [ "/entry.sh" ]
CMD [ "lambda_function.handler" ]