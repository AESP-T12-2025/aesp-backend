import json
from collections import defaultdict

with open('api_verification_report.json', 'r') as f:
    data = json.load(f)

# Group backend_only by router
backend_by_router = defaultdict(list)
for endpoint in data['backend_only']:
    if endpoint.get('backend'):
        router = endpoint['backend'][0]['router']
        backend_by_router[router].append(endpoint['backend'][0])

# Group frontend_only by service
frontend_by_service = defaultdict(list)
for endpoint in data['frontend_only']:
    if endpoint.get('frontend'):
        service = endpoint['frontend'][0]['service']
        frontend_by_service[service].append(endpoint['frontend'][0])

print("="*100)
print("BACKEND ONLY (56) - GROUPED BY ROUTER")
print("="*100)

for router, endpoints in sorted(backend_by_router.items(), key=lambda x: -len(x[1])):
    print(f"\n📂 {router.upper()} ({len(endpoints)} endpoints):")
    for ep in endpoints:
        print(f"   {ep['method']:<6} {ep['path']}")

print("\n" + "="*100)
print("FRONTEND ONLY (32) - GROUPED BY SERVICE")
print("="*100)

for service, endpoints in sorted(frontend_by_service.items(), key=lambda x: -len(x[1])):
    print(f"\n📂 {service} ({len(endpoints)} calls):")
    for ep in endpoints:
        print(f"   {ep['method']:<6} {ep['path']}")
