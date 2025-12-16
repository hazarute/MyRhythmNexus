import requests
import sys

BASE = "http://localhost:8000"

ids = [
    "363ed76b-182f-42f6-93bd-168be9946a8c",
    "167fd1c0-76aa-430a-8360-a9761e254886",
]

def get_member(member_id):
    url = f"{BASE}/api/v1/members/{member_id}"
    r = requests.get(url)
    return r.status_code, r.text

def list_members(include_inactive=False):
    params = {}
    if include_inactive:
        params['include_inactive'] = 'true'
    url = f"{BASE}/api/v1/members/"
    r = requests.get(url, params=params)
    return r.status_code, r.json() if r.status_code==200 else r.text

if __name__ == '__main__':
    print('Checking individual members by ID:')
    for mid in ids:
        status, body = get_member(mid)
        print(f'- {mid}: status={status}')
        if status==200:
            print(body)

    print('\nListing members (include_inactive=False):')
    s, data = list_members(False)
    print('status=', s, 'count=', len(data) if isinstance(data, list) else 'error')

    print('\nListing members (include_inactive=True):')
    s, data = list_members(True)
    print('status=', s, 'count=', len(data) if isinstance(data, list) else 'error')

    # Check if target IDs present in the returned lists
    def find_in_list(lst, mid):
        for u in lst:
            if u.get('id') == mid:
                return True
        return False

    if isinstance(data, list):
        for mid in ids:
            found = find_in_list(data, mid)
            print(f'Found {mid} in include_inactive list: {found}')
