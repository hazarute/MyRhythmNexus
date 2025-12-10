from pathlib import Path
from typing import Optional
try:
    import requests
except Exception:
    requests = None


def create_release_and_upload(repo: str, token: str, version: str, asset_path: Path, dry_run: bool = False) -> bool:
    if requests is None:
        print('requests module not available; install with: pip install requests')
        return False
    api_base = 'https://api.github.com'
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    tag = f'v{version}'
    print(f'Creating release {tag} in {repo}...')
    if dry_run:
        print('DRY-RUN: would create release and upload asset', asset_path)
        return True
    payload = {'tag_name': tag, 'name': tag, 'body': f'Release {tag} (automated)', 'prerelease': False}
    resp = requests.post(f'{api_base}/repos/{repo}/releases', headers=headers, json=payload, timeout=30)
    if resp.status_code == 201:
        release = resp.json()
    elif resp.status_code == 422:
        print('Release already exists, finding existing release...')
        r = requests.get(f'{api_base}/repos/{repo}/releases/tags/{tag}', headers=headers, timeout=30)
        if r.status_code != 200:
            print('Failed to fetch existing release:', r.status_code, r.text)
            return False
        release = r.json()
    else:
        print('Failed to create release:', resp.status_code, resp.text)
        return False
    upload_url = release.get('upload_url', '')
    if '{' in upload_url:
        upload_url = upload_url.split('{')[0]
    headers_upload = {'Authorization': f'token {token}', 'Content-Type': 'application/octet-stream'}
    params = {'name': asset_path.name}
    with open(asset_path, 'rb') as f:
        up = requests.post(upload_url, headers=headers_upload, params=params, data=f, timeout=60)
    if up.status_code in (201, 200):
        print('Asset uploaded successfully.')
        return True
    else:
        print('Asset upload failed:', up.status_code, up.text)
        return False
