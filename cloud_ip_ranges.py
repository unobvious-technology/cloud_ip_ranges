#!/usr/bin/python3

from argparse import ArgumentParser
import requests
from netaddr import IPNetwork, IPAddress
from lxml import html
import csv
import coloredlogs
import logging


def match_aws(target_ip):
    matched = False
    try:
        logger.info('Checking for AWS')
        aws_url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'
        aws_ips = requests.get(aws_url, allow_redirects=True).json()

        for item in aws_ips["prefixes"]:
            if target_ip in IPNetwork(str(item["ip_prefix"])):
                matched = True
                logger.info('Match for AWS range "{}", region "{}" and service "{}"'.format(
                    item['ip_prefix'],
                    item['region'],
                    item['service']
                ))

    except Exception as e:
        logger.error('Error: {}'.format(e))

    return matched


def match_azure(target_ip):
    matched = False
    try:
        logger.info('Checking for Azure')
        azure_url = 'https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519'
        page = requests.get(azure_url)
        tree = html.fromstring(page.content)
        download_url = tree.xpath("//a[contains(@class, 'failoverLink') and "
                                  "contains(@href,'download.microsoft.com/download/')]/@href")[0]

        azure_ips = requests.get(download_url, allow_redirects=True).json()

        for item in azure_ips["values"]:
            for prefix in item["properties"]['addressPrefixes']:
                if target_ip in IPNetwork(str(prefix)):
                    matched = True
                    logger.info('Match for Azure range "{}", region "{}" and service "{}"'.format(
                        prefix,
                        item["properties"]["region"],
                        item["properties"]["systemService"]
                    ))

    except Exception as e:
        logger.error('Error: {}'.format(e))

    return matched


def match_gcp(target_ip):
    matched = False
    try:
        logger.info('Checking for GCP')
        gcp_url = 'https://www.gstatic.com/ipranges/cloud.json'
        gcp_ips = requests.get(gcp_url, allow_redirects=True).json()

        for item in gcp_ips["prefixes"]:
            if target_ip in IPNetwork(str(item.get("ipv4Prefix", item.get("ipv6Prefix")))):
                matched = True
                logger.info('Match for GCP range "{}", region "{}" and service "{}"'.format(
                    item.get("ipv4Prefix", item.get("ipv6Prefix")),
                    item['scope'],
                    item['service']
                ))

    except Exception as e:
        logger.error('Error: {}'.format(e))

    return matched


def match_oci(target_ip):
    matched = False
    try:
        logger.info('Checking for OCI')
        oci_url = 'https://docs.cloud.oracle.com/en-us/iaas/tools/public_ip_ranges.json'
        oci_ips = requests.get(oci_url, allow_redirects=True).json()

        for region in oci_ips["regions"]:
            for cidr_item in region['cidrs']:
                if target_ip in IPNetwork(str(cidr_item["cidr"])):
                    matched = True
                    logger.info('Match for OCI range "{}", region "{}" and service "{}"'.format(
                        cidr_item['cidr'],
                        region['region'],
                        cidr_item["tags"][-1]
                    ))

    except Exception as e:
        logger.error('Error: {}'.format(e))

    return matched


def match_do(target_ip):
    matched = False
    try:
        logger.info('Checking for DigitalOcean')

        # This is the file linked from the digitalocean platform documentation website:
        # https://www.digitalocean.com/docs/platform/
        do_url = 'http://digitalocean.com/geo/google.csv'
        do_ips_request = requests.get(do_url, allow_redirects=True)

        do_ips = csv.DictReader(do_ips_request.content.decode('utf-8').splitlines(), fieldnames=[
            'range', 'country', 'region', 'city', 'postcode'
        ])

        for item in do_ips:
            if target_ip in IPNetwork(item['range']):
                matched = True
                logger.info('Match for DigitalOcean range "{}", country "{}", state "{}" and address "{} {}"'.format(
                    item['range'],
                    item['country'],
                    item['region'],
                    item['city'],
                    item['postcode']
                ))

    except Exception as e:
        logger.error('Error: {}'.format(e))

    return matched


logger = logging.getLogger(__name__)
coloredlogs.install(level='info')

if __name__ == "__main__":
    parser = ArgumentParser(add_help=True, allow_abbrev=False)

    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
                        help="Suppress logging output")
    parser.add_argument('ip',
                        help="The IP to evaluate, e.g.: 8.8.8.8")

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel('CRITICAL')

    target_ip = IPAddress(args.ip)

    logger.info('Starting IP check for: {}'.format(target_ip))

    matches = [
        match_aws(target_ip),
        match_azure(target_ip),
        match_gcp(target_ip),
        match_oci(target_ip),
        match_do(target_ip)
    ]

    logger.info('Done')

    if any(matches):
        exit(1)
    else:
        exit(0)
