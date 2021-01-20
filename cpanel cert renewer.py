import json
import sys, os, time
import subprocess
import http.client
import urllib.parse

config = None
cpanel = None
acme = None

class color:
    purple = "\033[35m"
    yellow = "\033[33m"
    green = "\033[32m"
    cyan = "\033[36m"
    blue = "\033[34m"
    red = "\033[31m"
    end = "\033[m"

class cpanelConn:
    def __init__(self, cpaneladdr, user, token):
        self.cpaneladdr = cpaneladdr
        self.headers = {"authorization": "cpanel " + user+":"+token}
    
    def ZoneEdit_fetchzone_records(self, line, domain):
        print("connecting to:", self.cpaneladdr+":2083")
        conn = http.client.HTTPSConnection(self.cpaneladdr+":2083")
        
        print("request: fetchzone_records")
        conn.request(method="GET", url="/json-api/cpanel?cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=ZoneEdit&cpanel_jsonapi_func=fetchzone_records&domain="+domain+"&line="+str(line), headers=self.headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        print("response:\n" + color.purple + data + color.end)
        return data

    def ZoneEdit_edit_zone_record(self, line, domain, name, type, txtdata):
        infoRecords = self.ZoneEdit_fetchzone_records(line, domain)
        
        if "_acme-challenge" in infoRecords:
            print("connecting to:", self.cpaneladdr+":2083")
            conn = http.client.HTTPSConnection(self.cpaneladdr+":2083")

            print("request: edit_zone_record")
            conn.request(method="GET", url="/json-api/cpanel?cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=ZoneEdit&cpanel_jsonapi_func=edit_zone_record&line="+str(line)+"&domain="+domain+"&name="+name+"&type="+type+"&txtdata="+txtdata, headers=self.headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            print("response:\n" + color.purple + data + color.end)
        else:
            print(color.red + "error: \"_acme-challenge\" not found in record name" + color.end)
            sys.exit()

    def SSL_installssl(self, cert, key):
        cert = urllib.parse.quote_plus(cert)
        key = urllib.parse.quote_plus(key)

        print("connecting to:", self.cpaneladdr+":2083")
        conn = http.client.HTTPSConnection(self.cpaneladdr + ":2083")

        print("request: installssl")
        conn.request(method="POST", url="/json-api/cpanel?cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=SSL&cpanel_jsonapi_func=installssl&crt="+cert+"&key="+key, headers=self.headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        print("SSL_installssl result: " + color.purple + data + color.end)

class acmeCertifier:        
    def findDomainTxtValues(self, rawdata):
        domains = []
        txtvalues = []
        lines = rawdata.splitlines()
        for line in lines:
            if "Domain: " in line:
                domains.append(line.split("'")[1])
            if "TXT value: " in line:
                txtvalues.append(line.split("'")[1])
        return domains, txtvalues
    
    def getCert(self, domain):
        with open(os.path.join(config["acmefold"], domain, domain+".key"), "r") as f:
            key = f.read()
        with open(os.path.join(config["acmefold"], domain, domain+".cer"), "r") as f:
            cert = f.read()
        return key, cert

def installCert(domain):
    print(color.green + "cert found!"  + color.end)
    key, cert = acme.getCert(domain)
    print(key, cert, sep="\n")

    print("installing ssl cert... ", end="")
    cpanel.SSL_installssl(cert, key)
    print(color.green + domain, "DONE" + color.end)

def main():
    global config, cpanel, acme
    print("loading config")
    config = json.load(open("config.json", "r"))
    cpanel = cpanelConn(config["cpanel"], config["user"], config["token"])
    acme = acmeCertifier()

    for domain in config["domains"]:
        print("removing:", domain)
        output = subprocess.run([config["acmepath"], "--remove", "-d", domain], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        print(color.cyan + output + color.end)
    
    for domain in config["domains"]:
        print("*" * len(domain) + "****")
        print("* " + domain + " *")
        print("*" * len(domain) + "****")

        print("issuing:", domain)
        issueCommand = [config["acmepath"], "--issue", "-d", domain, "-d", "*."+domain, "--dns", "--yes-I-know-dns-manual-mode-enough-go-ahead-please"]
        print(color.blue + " ".join(issueCommand) + color.end)
        output = subprocess.run(issueCommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        print(color.cyan + output + color.end)

        if "Cert success." in output:
            installCert(domain)
            continue

        elif "Add the following TXT record:" in output:
            print("found txt record")
            domainValues, txtValues = acme.findDomainTxtValues(output)  # domainValue = _acme-challenge.sub.domain.com
            print("domainTxtValues:\n", domainValues, "\n", txtValues)

            for n in range(len(domainValues)):
                print("zone record edit:", domainValues[n])
                mainDomain = ".".join(domainValues[n].split(".")[-2:])
                acmeChallengeSubDomain = ".".join(domainValues[n].split(".")[:-2])
                print("mainDomain:", mainDomain, "\nacmeChallengeSubDomain:", acmeChallengeSubDomain)
                cpanel.ZoneEdit_edit_zone_record(config["dnsZoneLine"][n], mainDomain, acmeChallengeSubDomain, "TXT", txtValues[n])
            
            print("waiting for propagation...")
            time.sleep(180)

            print("renewing for verification:", domain)
            renewCommand = [config["acmepath"], "--renew", "-d", domain, "--yes-I-know-dns-manual-mode-enough-go-ahead-please"]
            print(color.blue + " ".join(renewCommand) + color.end)
            output = subprocess.run(renewCommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
            print(color.cyan + output + color.end)

            if "Cert success." in output:
                installCert(domain)
            
            else:
                print(color.red + "cert not found" + color.end)

        else:
            print(color.red + "unexpected output... skipping" + color.end)
            continue

if __name__ == "__main__":
    main()