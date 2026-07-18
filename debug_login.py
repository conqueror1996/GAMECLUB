#!/usr/bin/env python3
"""Test login across all base URLs to find working one."""
import requests
import re
from bs4 import BeautifulSoup

URLS = [
    "https://starexch555.com",
    "https://cricmatch247.com",
    "https://khelstake24.com",
    "https://playcric365.com",
]
USERNAME = "Ravichamar"
PASSWORD = "Tutar7618&"

for BASE_URL in URLS:
    print(f"\n{'='*50}")
    print(f"TRYING: {BASE_URL}")
    print(f"{'='*50}")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    })

    try:
        resp = session.get(f"{BASE_URL}/login", timeout=15)
        print(f"  GET /login → {resp.status_code}")

        soup = BeautifulSoup(resp.text, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        csrf = token_input.get('value') if token_input else None
        if not csrf:
            meta = soup.find('meta', {'name': 'csrf-token'})
            csrf = meta.get('content') if meta else None
        
        if not csrf:
            print("  ❌ No CSRF token found, skipping")
            continue

        session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/login",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        })

        resp_login = session.post(f"{BASE_URL}/login", data={
            "username": USERNAME,
            "password": PASSWORD,
            "remember_me": "1",
            "_token": csrf
        }, timeout=15)

        login_json = resp_login.json()
        status = login_json.get('status')
        message = login_json.get('message', '')
        print(f"  POST /login → status={status}, message={message}")

        if status == 200:
            print(f"\n  ✅ LOGIN SUCCESS on {BASE_URL}!")
            
            session.headers.pop("X-Requested-With", None)
            session.headers.pop("Content-Type", None)
            session.headers.update({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
            
            resp_launcher = session.get(f"{BASE_URL}/7mojos/launcher?q=427", timeout=15)
            print(f"  Launcher URL: {resp_launcher.url[:200]}")
            
            pt = re.search(r'playerToken=([^&"\']+)', resp_launcher.url)
            ot = re.search(r'operatorToken=([^&"\']+)', resp_launcher.url)
            
            if pt and ot:
                print(f"\n  playerToken:   {pt.group(1)}")
                print(f"  operatorToken: {ot.group(1)}")
                print(f"\n  Run discovery with:")
                print(f"  ./venv/bin/python discover_ab_direct.py '{pt.group(1)}' '{ot.group(1)}'")
            break
        else:
            print(f"  ❌ Failed: {message}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
