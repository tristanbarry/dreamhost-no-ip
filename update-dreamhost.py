#!/usr/bin/python
import os
import argparse
import urllib.parse
import urllib.request
import sys
import json
import datetime
import subprocess

parser = argparse.ArgumentParser(
    description="Update subdomains usng the dreamhost API."
)
parser.add_argument(
    "--get-ip",
    dest="get_ip",
    help="Get external ip address and exit",
    action="store_true",
)
parser.add_argument(
    "--domain",
    help="Full domain name to update. ex: `abc.onetwothree.com`, where \
    `onetwothree.com` dns is controlled by Dreamhost",
)
parser.add_argument(
    "--ip",
    help="Ip to use for update (if omitted, will use your external ip for the update",
)
parser.add_argument("--apikey", help="Dreamhost API key with dns permissions.")
args = parser.parse_args()

DOMAIN = args.domain
DREAMHOST_KEY = args.apikey or os.environ.get("APIKEY")
DREAMHOST_DEFAULT_PARAMS = {"key": DREAMHOST_KEY, "format": "json"}

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def request(params, action=""):
    url = "https://api.dreamhost.com/?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            parsed = json.loads(data.decode("utf-8"))
            if parsed.get("result") != "success":
                raise Exception()
            return parsed
    except:
        print(": ".join([now, "Error from dreamworks api.", action]))
        sys.exit(-1)


def get_ip():
    output = subprocess.check_output(
        "dig +short myip.opendns.com @resolver1.opendns.com".split(" ")
    )
    return output.strip().decode("utf-8")


def get_dns_record(domain):
    params = DREAMHOST_DEFAULT_PARAMS.copy()
    params["cmd"] = "dns-list_records"
    dns_data = request(params, "get_dns_record")
    fqdn = domain.lower()
    return next((r for r in dns_data["data"] if r["record"].lower() == fqdn), None)


def add_dns_record(domain, ip):
    params = DREAMHOST_DEFAULT_PARAMS.copy()
    params["cmd"] = "dns-add_record"
    params["record"] = domain.lower()
    params["type"] = "A"
    params["comment"] = "autoupdated on " + now
    params["value"] = ip
    request(params, "add_dns_record")


def remove_dns_record(record):
    params = DREAMHOST_DEFAULT_PARAMS.copy()
    params["cmd"] = "dns-remove_record"
    params["record"] = record.get("record")
    params["type"] = record.get("type")
    params["value"] = record.get("value")
    request(params, "remove_dns_record")


if __name__ == "__main__":
    if args.get_ip:
        print(now, get_ip())
        sys.exit()

    if not DOMAIN:
        print(now, "no domain to update")
        sys.exit()

    if not DREAMHOST_KEY:
        print("No API key provided")
        sys.exit(-1)

    ip = args.ip if args.ip else get_ip()
    record = get_dns_record(args.domain)

    if not record:
        print(
            now,
            "DNS record for",
            DOMAIN,
            "does not exist, setting to",
            ip,
            "... ",
            end="",
        )
        add_dns_record(DOMAIN, ip)
        print("done.")
        sys.exit()

    dns_ip = record.get("value", "").strip()
    if dns_ip == ip.strip():
        print(now, "nothing to update.", DOMAIN, "is set to", ip)
        sys.exit()

    print(now, "Updating record", DOMAIN, "from", dns_ip, "to", ip, "...", end="")
    remove_dns_record(record)
    add_dns_record(DOMAIN, ip)
    print("done")
