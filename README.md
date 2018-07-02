# update-dreamhost 

Creates dns records using the Dreamhost API. This is a home-brewed version of no-ip for people with Dreamhost accounts.

Works with Python 3.

# Usage

Print your external IP address
```
python update-dreamhost.py --get-ip  
```


Update the Dreamhost record.
Note: you can pass your Dreamhost API key by setting an `APIKEY` environment variable, or a parameter
```
python update-dreamhost.py --domain subdomain.domain.tld --apikey abc123

-- or --

APIKEY=123 python update-dreamhost.py --domain subdomain.domain.tld 
```
 
This script auto-detects your external ip address, but you can bypass this and manually set it with the `ip` flag:
```
APIKEY=123 python update-dreamhost.py --domain subdomain.domain.tld --ip 1.2.3.4
```

