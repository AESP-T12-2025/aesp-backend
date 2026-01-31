import json

with open('api_verification_report.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("BACKEND ONLY - ALL 56 ENDPOINTS:")
print("=" * 80)

for i, endpoint in enumerate(data['backend_only'], 1):
    backends = endpoint.get('backend', [])
    if backends:
        b = backends[0]
        print(f"{i:2}. {b['method']:<6} {b['path']:<65} ({b['router']})")

print("\n" + "=" * 80)
print("FRONTEND ONLY - ALL 32 ENDPOINTS:")
print("=" * 80)

for i, endpoint in enumerate(data['frontend_only'], 1):
    frontends = endpoint.get('frontend', [])
    if frontends:
        f = frontends[0]
        print(f"{i:2}. {f['method']:<6} {f['path']:<65} ({f['service']})")
