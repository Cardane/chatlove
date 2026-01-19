import json

# Load HAR file
with open('lovable.dev.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

# Find POST requests to api.lovable.dev
post_entries = [e for e in entries if e['request']['method'] == 'POST' and 'api.lovable.dev' in e['request']['url']]

print(f'Total POST API entries: {len(post_entries)}\n')

for entry in post_entries[:3]:
    print(f"URL: {entry['request']['url']}")
    print("Headers:")
    for header in entry['request']['headers']:
        if header['name'].lower() in ['authorization', 'content-type', 'x-client-git-sha', 'cookie']:
            value = header['value']
            if len(value) > 100:
                value = value[:100] + '...'
            print(f"  {header['name']}: {value}")
    
    if 'postData' in entry['request']:
        print(f"Body: {entry['request']['postData'].get('text', 'N/A')[:200]}")
    
    print("\n" + "="*80 + "\n")
