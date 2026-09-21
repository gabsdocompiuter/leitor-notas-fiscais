#!/bin/bash

git fetch origin
git pull

docker compose up -d --build
