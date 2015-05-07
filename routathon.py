#!/usr/bin/env python

import argparse
from collections import namedtuple
import json

from boto.ec2.elb import connect_to_region
from jinja2 import Environment, FileSystemLoader
import marathon


Frontend = namedtuple('Frontend', ['id', 'protocol', 'port', 'backends'])
Backend = namedtuple('Backend', ['id', 'host', 'port'])


class ProxyRule(object):

    def __init__(self, app_id, protocol, app_port, haproxy_port, acl=None):
        self.app_id = app_id
        self.protocol = protocol
        self.app_port = app_port
        self.haproxy_port = haproxy_port
        self.acl = acl

    @classmethod
    def from_json(cls, obj):
        return [
            ProxyRule(r[0], r[1], r[2], r[3]) if len(r) < 5 else
            ProxyRule(r[0], r[1], r[2], r[3], r[4])
            for r in obj

        ]


def update_listeners(region_name, elb_name, proxy_rules):
    c = connect_to_region(region_name)
    c.create_load_balancer_listeners(elb_name, [(p.haproxy_port, p.haproxy_port, p.protocol) for p in proxy_rules])


def sanitize(app_id):
    return app_id.replace('/', ':')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='marathon_url', required=True, help='Marathon server URL (http[s]://<host>:<port>)')
    parser.add_argument('-r', dest='rules', required=True,
        help='JSON array of (app name, protocol, HAProxy port, app port) tuples (e.g., \'[["myapp", "tcp", 8081, 80]]\'')
    parser.add_argument('-t', dest='template', required=True, help='Path to Jinja2 template to render')
    parser.add_argument('-o', dest='output_file', help='Where to write the rendered template (if unset, print to stdout)')

    aws_args = parser.add_argument_group('AWS arguments')
    aws_args.add_argument('--elb', dest='elb', help='Name of the AWS ELB on which to update listeners')
    aws_args.add_argument('--region', dest='region', help='AWS region of the ELB')

    args = parser.parse_args()
    rules = ProxyRule.from_json(json.loads(args.rules))

    m = marathon.MarathonClient(args.marathon_url)
    endpoints = m.list_endpoints()

    # Sort to ensure template renders consistently
    endpoints.sort(key=lambda e: e.task_id)

    frontends = [
        Frontend(sanitize(r.app_id), r.protocol, r.haproxy_port,
            [Backend(e.task_id, e.host, e.task_port)
            for e in endpoints if e.app_id == r.app_id and e.service_port == r.app_port]
        ) for r in rules
    ]

    env = Environment(loader=FileSystemLoader('/'))
    template = env.get_template(args.template)

    rendered_template = template.render(frontends=frontends)
    if args.output_file:
        with open(args.output_file, 'wb') as fh:
            fh.write(rendered_template)
    else:
        print rendered_template

    if args.elb and args.region:
        update_listeners(args.region, args.elb, rules)


if __name__ == '__main__':
    main()