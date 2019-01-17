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
    help="Get external dns record and exit",
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
parser.add_argument(
    "--dns-file",
    help="File to start the dns state. If it does not exist it will be created. Default 'dns-record.txt'"
)
parser.add_argument("--apikey", help="Dreamhost API key with dns permissions.")
args = parser.parse_args()

DOMAIN = args.domain
DREAMHOST_KEY = args.apikey or os.environ.get("APIKEY")
DREAMHOST_DEFAULT_PARAMS = {"key": DREAMHOST_KEY, "format": "json"}
DNS_RECORD_FILE = args.dns_file or 'dns-record.txt'

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def request(params, action=""):
    url = "https://api.dreamhost.com/?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            parsed = json.loads(data.decode("utf-8"))
            if parsed.get("result") != "success":
                raise Exception(parsed)
            return parsed
    except Exception as e:
        print(": ".join([now, "Error from dreamworks api.", action]))
        print(e)
        sys.exit(-1)


def get_ip():
    output = subprocess.check_output(
        "dig +short myip.opendns.com @resolver1.opendns.com".split(" ")
    )
    return output.strip().decode("utf-8")


def read_state_file(filename):
    """
    Try to get the domain from a file. Assume the file is
    always up to date. If it doesn't exist, the dns record is created/updated.
    """
    f = None
    try:
        f = open(filename, 'r')
        return json.loads(f.read())
    except:
        return {}
    finally:
        if f:
            f.close()

def write_state_file(filename, state):
    state_str = json.dumps(state)
    f = open(filename, 'w')
    f.write(state_str)

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
    if not record:
        return
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
    state = read_state_file(DNS_RECORD_FILE)
    domain_ip = state.get(DOMAIN)

    if not domain_ip:
        print(
            now,
            "DNS record for",
            DOMAIN,
            "does not exist, setting to",
            ip,
            "... ",
            end="",
        )

        # Update remote dns (possibly remove it first if the state file didn't exist)
        record = get_dns_record(args.domain)
        remove_dns_record(record)
        add_dns_record(DOMAIN, ip)
        # Update local state
        state[DOMAIN] = ip
        write_state_file(DNS_RECORD_FILE, state)
        print("done.")
        sys.exit()

    if domain_ip == ip.strip():
        print(now, "nothing to update.", DOMAIN, "is set to", ip)
        sys.exit()

    print(now, "Updating record", DOMAIN, "from", domain_ip, "to", ip, "...", end="")
    # Update remote dns
    record = get_dns_record(args.domain)
    remove_dns_record(record)
    add_dns_record(DOMAIN, ip)
    # Update local state
    state[DOMAIN] = ip
    write_state_file(DNS_RECORD_FILE, state)
    print("done")
