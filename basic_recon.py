import sys
import subprocess
import os

def whois(target):
    r= subprocess.run(f"whois {target}",shell=True)
    print(f"Results for whois on {target}:\n",r)

def nslookup(target):
    r2 = subprocess.run(f"nslookup {target}",shell=True,capture_output=True, text=True)
    print(f"Results for nslookup on {target} :\n",r2.stdout())

def httpx(target):
    r3 = subprocess.run(f"httpx {target}",shell=True,capture_output=True, text=True)
    print(f"Results for httpx on {target}: \n", r3.stdout())



target=input("Enter ip/url:")
print(f"Starting basic recon on {target}, tools being used - whois,nslookup,httpx")
whois(target)
nslookup(target)
httpx(target)