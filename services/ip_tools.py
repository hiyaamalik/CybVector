import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

VT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")

HEADERS_VT = {"x-apikey": VT_API_KEY} if VT_API_KEY else {}
HEADERS_ABUSE = {"Accept": "application/json", "Key": ABUSEIPDB_API_KEY} if ABUSEIPDB_API_KEY else {}

def check_ip_virustotal(ip):
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    try:
        r = requests.get(url, headers=HEADERS_VT, timeout=15)
        if r.status_code == 200:
            attrs = r.json().get("data", {}).get("attributes", {})
            return {
                "ok": True,
                "source": "VirusTotal",
                "type": "ip",
                "ip": ip,
                "reputation": attrs.get("reputation"),
                "last_analysis_stats": attrs.get("last_analysis_stats", {})
            }
        return {"ok": False, "source": "VirusTotal", "error": r.text}
    except Exception as e:
        return {"ok": False, "source": "VirusTotal", "error": str(e)}

def check_ip_abuseipdb(ip):
    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": "90"}
    try:
        r = requests.get(url, headers=HEADERS_ABUSE, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", {})
            return {
                "ok": True,
                "source": "AbuseIPDB",
                "type": "ip",
                "ip": ip,
                "abuseConfidenceScore": data.get("abuseConfidenceScore"),
                "totalReports": data.get("totalReports")
            }
        return {"ok": False, "source": "AbuseIPDB", "error": r.text}
    except Exception as e:
        return {"ok": False, "source": "AbuseIPDB", "error": str(e)}

def check_domain_virustotal(domain):
    url = f"https://www.virustotal.com/api/v3/domains/{domain}"
    try:
        r = requests.get(url, headers=HEADERS_VT, timeout=15)
        if r.status_code == 200:
            attrs = r.json().get("data", {}).get("attributes", {})
            return {
                "ok": True,
                "source": "VirusTotal",
                "type": "domain",
                "domain": domain,
                "reputation": attrs.get("reputation"),
                "last_analysis_stats": attrs.get("last_analysis_stats", {})
            }
        return {"ok": False, "source": "VirusTotal", "error": r.text}
    except Exception as e:
        return {"ok": False, "source": "VirusTotal", "error": str(e)}

def check_url_virustotal(url_to_check):
    try:
        url_id = base64.urlsafe_b64encode(url_to_check.encode()).decode().strip("=")
        url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        r = requests.get(url, headers=HEADERS_VT, timeout=15)
        if r.status_code == 200:
            attrs = r.json().get("data", {}).get("attributes", {})
            return {
                "ok": True,
                "source": "VirusTotal",
                "type": "url",
                "url": url_to_check,
                "reputation": attrs.get("reputation"),
                "last_analysis_stats": attrs.get("last_analysis_stats", {})
            }
        return {"ok": False, "source": "VirusTotal", "error": r.text}
    except Exception as e:
        return {"ok": False, "source": "VirusTotal", "error": str(e)}
