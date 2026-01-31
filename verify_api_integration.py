"""
API Integration Verification Script
=====================================
Systematically scans all backend routers and frontend services
to verify complete and correct API integration.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Paths
BACKEND_ROUTERS = Path("app/routers")
FRONTEND_SERVICES = Path("../aesp-frontend/src/services")

def extract_backend_endpoints(router_file):
    """Extract all endpoints from a backend router file."""
    endpoints = []
    
    with open(router_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
    router_name = router_file.stem
    
    # Find router prefix
    prefix_match = re.search(r'router\s*=\s*APIRouter\([^)]*prefix=["\']([^"\']+)', content)
    prefix = prefix_match.group(1) if prefix_match else f"/{router_name}"
    
    # Find all decorator patterns
    pattern = r'@router\.(get|post|put|patch|delete|options)\(["\']([^"\']+)["\']'
    
    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            method = match.group(1).upper()
            path = match.group(2)
            
            # Get function name
            func_match = None
            for j in range(i+1, min(i+10, len(lines))):
                func_match = re.match(r'(async\s+)?def\s+(\w+)', lines[j])
                if func_match:
                    break
            
            func_name = func_match.group(2) if func_match else "unknown"
            full_path = prefix + path
            
            endpoints.append({
                'method': method,
                'path': full_path,
                'function': func_name,
                'router': router_name,
                'line': i + 1
            })
    
    return endpoints

def extract_frontend_methods(service_file):
    """Extract all API calls from a frontend service file."""
    methods = []
    
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    service_name = service_file.stem
    
    # Pattern for api calls: api.get('/path')
    pattern = r'api\.(get|post|put|patch|delete|options)\([\'"]([^\'"]+)'
    
    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            http_method = match.group(1).upper()
            path = match.group(2)
            
            # Find enclosing function
            func_name = "unknown"
            for j in range(i-1, max(0, i-20), -1):
                func_match = re.match(r'\s+(\w+):\s*async', lines[j])
                if func_match:
                    func_name = func_match.group(1)
                    break
            
            methods.append({
                'method': http_method,
                'path': path,
                'function': func_name,
                'service': service_name,
                'line': i + 1
            })
    
    return methods

def normalize_path(path):
    """Normalize path for comparison (replace params)."""
    # Replace {id}, {user_id}, etc with generic placeholder
    normalized = re.sub(r'\{[^}]+\}', '{PARAM}', path)
    normalized = re.sub(r'\$\{[^}]+\}', '{PARAM}', normalized)
    # Remove trailing slash
    normalized = normalized.rstrip('/')
    return normalized

def main():
    print("🔍 API Integration Verification")
    print("=" * 80)
    
    # Scan backend
    print("\n📡 Scanning backend routers...")
    backend_endpoints = []
    backend_files = list(BACKEND_ROUTERS.glob("*.py"))
    backend_files = [f for f in backend_files if f.name != "__init__.py"]
    
    for router_file in sorted(backend_files):
        endpoints = extract_backend_endpoints(router_file)
        backend_endpoints.extend(endpoints)
        print(f"  ✓ {router_file.stem:20s} - {len(endpoints):3d} endpoints")
    
    print(f"\n  Total backend endpoints: {len(backend_endpoints)}")
    
    # Scan frontend
    print("\n💻 Scanning frontend services...")
    frontend_methods = []
    frontend_files = list(FRONTEND_SERVICES.glob("*Service.ts"))
    
    for service_file in sorted(frontend_files):
        methods = extract_frontend_methods(service_file)
        frontend_methods.extend(methods)
        print(f"  ✓ {service_file.stem:25s} - {len(methods):3d} API calls")
    
    print(f"\n  Total frontend API calls: {len(frontend_methods)}")
    
    # Cross-check
    print("\n🔗 Cross-checking integration...")
    
    # Build lookup dicts
    backend_map = defaultdict(list)
    for ep in backend_endpoints:
        key = (ep['method'], normalize_path(ep['path']))
        backend_map[key].append(ep)
    
    frontend_map = defaultdict(list)
    for method in frontend_methods:
        key = (method['method'], normalize_path(method['path']))
        frontend_map[key].append(method)
    
    # Find matches and gaps
    matched = []
    backend_only = []
    frontend_only = []
    
    all_keys = set(backend_map.keys()) | set(frontend_map.keys())
    
    for key in sorted(all_keys):
        method, path = key
        
        in_backend = key in backend_map
        in_frontend = key in frontend_map
        
        if in_backend and in_frontend:
            matched.append({
                'method': method,
                'path': path,
                'backend': backend_map[key],
                'frontend': frontend_map[key]
            })
        elif in_backend and not in_frontend:
            backend_only.append({
                'method': method,
                'path': path,
                'backend': backend_map[key]
            })
        elif not in_backend and in_frontend:
            frontend_only.append({
                'method': method,
                'path': path,
                'frontend': frontend_map[key]
            })
    
    # Generate report
    print(f"\n📊 Results:")
    print(f"  ✅ Matched:        {len(matched):3d} endpoints")
    print(f"  ⚠️  Backend only:   {len(backend_only):3d} endpoints")
    print(f"  ❌ Frontend only:  {len(frontend_only):3d} endpoints (potential errors)")
    
    integration_rate = len(matched) / len(backend_map) * 100 if backend_map else 0
    print(f"\n  Integration Rate: {integration_rate:.1f}%")
    
    # Save detailed report
    report = {
        'summary': {
            'backend_endpoints': len(backend_endpoints),
            'frontend_methods': len(frontend_methods),
            'matched': len(matched),
            'backend_only': len(backend_only),
            'frontend_only': len(frontend_only),
            'integration_rate': round(integration_rate, 1)
        },
        'matched': matched,
        'backend_only': backend_only,
        'frontend_only': frontend_only
    }
    
    with open('api_verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: api_verification_report.json")
    
    # Print unintegrated endpoints
    if backend_only:
        print(f"\n🔴 UNINTEGRATED BACKEND ENDPOINTS ({len(backend_only)}):")
        print("=" * 80)
        
        by_router = defaultdict(list)
        for item in backend_only:
            router = item['backend'][0]['router']
            by_router[router].append(item)
        
        for router in sorted(by_router.keys()):
            items = by_router[router]
            print(f"\n  📁 {router}.py ({len(items)} endpoints):")
            for item in items[:10]:  # Show first 10
                print(f"     {item['method']:6s} {item['path']}")
            if len(items) > 10:
                print(f"     ... and {len(items) - 10} more")
    
    if frontend_only:
        print(f"\n⚠️  FRONTEND CALLS WITHOUT BACKEND ({len(frontend_only)}):")
        print("=" * 80)
        for item in frontend_only[:20]:
            service = item['frontend'][0]['service']
            print(f"  {service:25s} {item['method']:6s} {item['path']}")
        if len(frontend_only) > 20:
            print(f"  ... and {len(frontend_only) - 20} more")
    
    print("\n✅ Verification complete!")
    return report

if __name__ == "__main__":
    main()
