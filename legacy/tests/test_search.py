from modules import crud
from modules import paths
paths.ensure_directories()
records = crud.search('', '04-2026')
print(f'Found {len(records)} records')
for r in records:
    print(f'- {r.get("package_id")} {r.get("created_at")}')
    data = r.get('data', {})
    demo = data.get('demographics', {})
    print(f'  {demo.get("ho_ten", "?")}')