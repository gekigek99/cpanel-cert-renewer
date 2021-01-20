# cpanel-cert-renewer

This script is used to auto update the ssl certificates for your website by interacting with cpanel API and acme.sh

It is able to generate and install wildcard certificates for a domain and its subdomains

## set up procedure:
1) download acme.sh with `curl https://get.acme.sh | sh`
2) add "acmepath" and "acmefold" parameters to the config
3) add your cpanel address to "cpanel" parameter
4) add your cpanel username to "user" parameter
5) in cpanel generate a token and add it to "token" parameter
6) in cpanel in DNS zone editor add **2** TXT records called "_acme-challenge.<domain>"
7) after adding your info execute this curl request: `curl --request GET --url 'https://<cpanel address>:2083/json-api/cpanel?cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=ZoneEdit&cpanel_jsonapi_func=fetchzone_records&domain=<domain>' --header 'Authorization: cpanel <user>:<token>'`
8) look for the 2 records beginning with "_acme-challenge" and save their lines in the config in "dnsZoneLine" as a list
9) add the domain and relative subdomains

**you can now execute the python program!**

_(i advise you to run this program once a week with a cron job)_


#### Disclaimer:
I am not responsible for damages that this software might cause to your system or website.  
Be sure to understand the basics of how acme.sh and ssl certificates work before using this software.  
Read carefully the code to understand how it works and avoid problems.  
There might be important bugs related to the complicated matter this program has to manage.