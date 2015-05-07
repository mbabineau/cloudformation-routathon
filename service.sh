#!/bin/bash -e

MISSING_VAR_MESSAGE="must be set"
DEFAULT_CONFIG_TEMPLATE="us-west-2"
: ${S3_BUCKET:?$MISSING_VAR_MESSAGE}
: ${S3_PREFIX:?$MISSING_VAR_MESSAGE}
: ${HOSTNAME:?$MISSING_VAR_MESSAGE}
: ${AWS_REGION:=$DEFAULT_AWS_REGION}
MARATHON_URL=

while true; do
    CHECKSUM=$(md5sum /etc/haproxy/haproxy.cfg)

    /opt/
    -m {{ marathon_url }}
    -r ' { Ref : ProxyRules } '
    -t /etc/haproxy/haproxy.cfg.jinja2
    -o /etc/haproxy/haproxy.cfg
  if [[ ${CHECKSUM} != \`md5sum /etc/haproxy/haproxy.cfg`\ ]]; then
    echo 'Changes detected - reloading HAProxy config'
    service haproxy reload 2>&1
  fi
  sleep 5
done