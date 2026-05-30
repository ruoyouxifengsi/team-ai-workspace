FROM alpine:3.20
RUN apk add --no-cache tar findutils tini
COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh \
    && echo "0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/root
ENTRYPOINT ["/sbin/tini","--"]
CMD ["crond","-f","-l","8"]
