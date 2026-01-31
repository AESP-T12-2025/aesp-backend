import json

with open('api_verification_report.json', 'r') as f:
    data = json.load(f)

summary = data['summary']

print("=" * 80)
print("📊 API INTEGRATION VERIFICATION - PHASE 1 & 2 RESULTS")
print("=" * 80)
print(f"\n✅ Backend Endpoints:    {summary['backend_endpoints']}")
print(f"✅ Frontend Methods:     {summary['frontend_methods']}")
print(f"🔗 Matched:              {summary['matched']} ({summary['integration_rate']}%)")
print(f"❌ Backend Only:         {summary['backend_only']}")
print(f"⚠️  Frontend Only:        {summary['frontend_only']}")

print("\n" + "=" * 80)
print("🔴 MISSING ENDPOINTS (Backend Only - Top 30):")
print("=" * 80)

for i, endpoint in enumerate(data['backend_only'][:30], 1):
    backends = endpoint.get('backend', [])
    if backends:
        method = backends[0].get('method', 'N/A')
        path = backends[0].get('path', 'N/A')
        router = backends[0].get('router', 'N/A')
        line = backends[0].get('line', 'N/A')
        print(f"{i:2}. {method:<6} {path:<60} ({router}:{line})")

print("\n" + "=" * 80)
print("⚠️  FRONTEND-ONLY CALLS (May need verification - Top 20):")
print("=" * 80)

for i, call in enumerate(data['frontend_only'][:20], 1):
    frontends = call.get('frontend', [])
    if frontends:
        method = frontends[0].get('method', 'N/A')
        path = frontends[0].get('path', 'N/A')
        service = frontends[0].get('service', 'N/A')
        line = frontends[0].get('line', 'N/A')
        print(f"{i:2}. {method:<6} {path:<60} ({service}:{line})")

# Group backend_only by router
print("\n" + "=" * 80)
print("📋 MISSING BY ROUTER:")
print("=" * 80)

router_count = {}
for endpoint in data['backend_only']:
    backends = endpoint.get('backend', [])
    if backends:
        router = backends[0].get('router', 'unknown')
        router_count[router] = router_count.get(router, 0) + 1

for router, count in sorted(router_count.items(), key=lambda x: -x[1]):
    print(f"  {router:<20} {count:3} endpoints")
