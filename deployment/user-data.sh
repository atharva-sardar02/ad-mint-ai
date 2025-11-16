#!/bin/bash
# Bootstrap script for ad-mint-ai backend deployment
apt-get update
apt-get install -y git python3.11 python3.11-venv python3-pip nginx
mkdir -p /var/www/ad-mint-ai
chown ubuntu:ubuntu /var/www/ad-mint-ai
