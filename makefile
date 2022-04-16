#!/bin/make -f
IMAGE_NAME=latex_detector
IMAGE_TAG=v1
IMAGE_TEST_TAG=test
FULL_IMAGE_NAME=${IMAGE_NAME}:${IMAGE_TAG}
FULL_IMAGE_TEST_NAME=${IMAGE_NAME}:${IMAGE_TEST_TAG}
DATA_BUCKET=test
DATA_FILE=latex.pth
CONFIG_BUCKET=test
CONFIG_FILE=latex.py
MODEL_NAME=latex
DEVICE=cpu
SONAR_TEST_IMAGE="sonar_test_image"
SONAR_TEST_TAG="sonar_test_tag"

SHELL:=/bin/bash

.PHONY: build,test

build: Dockerfile
	docker build -f Dockerfile --target build . -t ${image_name}

test:
	docker build -f Dockerfile --target test . -t ${FULL_IMAGE_TEST_NAME}

sonar_test:
	echo "sonar project needs to be created"
