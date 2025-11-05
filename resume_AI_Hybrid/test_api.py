import requests
import json

# Test the database management API endpoints
base_url = "http://localhost:5001"

def test_api_endpoint(endpoint, method='GET', description=""):
    url = f"{base_url}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint} - {description}")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, timeout=5)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"📄 Response: {json.dumps(data, indent=2)}")
        else:
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Test the API endpoints
print("🧪 Testing ChromaDB Admin API Endpoints")
print("=" * 50)

# Test health check
test_api_endpoint("/api/database/health", "GET", "Health Check")

# Test stats
test_api_endpoint("/api/database/stats", "GET", "Database Statistics")

print("\n✅ API testing completed!")
print("\n📝 Instructions for manual testing:")
print("1. Open http://localhost:5001/admin/database in your browser")
print("2. Try the Health Check button")
print("3. Try the Clear All Collections button (with confirmation)")
print("4. Try the Reset Database button (with confirmation)")
print("5. Check that real data loads in the sidebar")