import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_endpoint(name, url, params=None):
    print(f"\n--- Testing {name} ---")
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    print(f"URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Status: {status}")
            data = json.loads(body)
            
            if 'events' in data:
                print(f"✅ Success. Found {len(data['events'])} events.")
                if len(data['events']) > 0:
                    print(f"Sample event: {data['events'][0]}")
            elif 'by_rule' in data:
                print(f"✅ Stats Success. Total: {data.get('total')}")
                print(json.dumps(data, indent=2))
            else:
                print("✅ Success:", str(data)[:200])
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print("Body:", e.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 1: Get Events
test_endpoint("Get All Events", f"{BASE_URL}/events", {"limit": 10})

# Test 2: Get Stats (The failing one)
test_endpoint("Get Stats (24h)", f"{BASE_URL}/events/stats", {"hours": 24})
