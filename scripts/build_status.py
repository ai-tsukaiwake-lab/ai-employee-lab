#!/usr/bin/env python3
"""Export a public allowlisted status and a private artifact bundle.
Never publish the private bundle or raw AI contents to GitHub Pages.
"""
import json
import os
from pathlib import Path

RESULT_DIR = Path('pipeline_results')
ROLE_FILES = ['00_status', '01_plan', '02_research_plan', '03_drafts', '04_audit', '05_operations', '06_analytics']
ALLOWED_STATES = {'COMPLETED_PENDING_HUMAN_REVIEW', 'FAILED_PARTIAL'}
ALLOWED_ROLES = {'企画AI', '調査AI', '制作AI', '監査AI', '運用AI（状態記録のみ）'}

def read(name):
    p = RESULT_DIR / (name + '.json')
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding='utf-8'))

def main():
    status = read('00_status')
    if not isinstance(status, dict):
        raise SystemExit('Missing or invalid 00_status.json; refusing to publish.')
    # Intentionally do not expose topic, account, model, timestamps, prompts, or contents.
    completed = status.get('completed_roles', [])
    if not isinstance(completed, list):
        completed = []
    public = {
        'schema': 'public-status-v1',
        'run_id': str(os.environ.get('GITHUB_RUN_ID', 'unknown'))[:24],
        'run_status': status.get('run_status') if status.get('run_status') in ALLOWED_STATES else 'UNKNOWN',
        'roles_completed': sum(1 for r in set(completed) if r in ALLOWED_ROLES),
        'total_roles': 6,
        'draft_count': max(0, min(20, int(status.get('total_drafts', 0) or 0))),
        'audited_count': max(0, min(20, int(status.get('audited_drafts', 0) or 0))),
        'human_approval': 'NOT_GRANTED',
        'x_posting': 'DISABLED',
        'details_public': False,
    }
    Path('public-status.json').write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # This never enters the repository; only uploaded as an Actions artifact.
    bundle = {'schema':'private-bundle-v1', 'files':{}}
    for key in ROLE_FILES:
        item = read(key)
        if item is not None:
            bundle['files'][key + '.json'] = item
    RESULT_DIR.mkdir(exist_ok=True)
    (RESULT_DIR/'bundle.json').write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Public allowlisted status generated; private bundle has {len(bundle['files'])} file entries.")

if __name__ == '__main__':
    main()
