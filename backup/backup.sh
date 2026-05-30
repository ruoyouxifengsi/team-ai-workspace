#!/bin/sh
set -e
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p /data/backups
tar -czf /data/backups/${TS}.tar.gz -C /data \
    --exclude=./backups \
    .
# retain 7 days
find /data/backups -name "*.tar.gz" -mtime +7 -delete
echo "backup ${TS} done"
