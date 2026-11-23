#!/usr/bin/env python3
"""Gemini connectivity diagnostic. Never writes credentials or generated text."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://generativelanguage.googleapis.com/v1beta'
OUT = Path('diagnostic_result.json')

def request(url, key, data=None):
    headers = {'x-goog-api-key': key}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers, method='POST' if data is not None else 'GET')
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        # Avoid echoing API response text (which may contain private request data).
        return e.code, None
    except (urllib.error.URLError, TimeoutError):
        return 'NETWORK_ERROR', None
    except (ValueError, json.JSONDecodeError):
        return 'INVALID_RESPONSE', None

key = os.environ.get('GEMINI_API_KEY', '').strip()
model = os.environ.get('DIAG_MODEL', 'gemini-3.5-flash-lite').strip()
result = {
    'diagnostic': 'gemini-connection-v1.2',
    'timestamp_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'model_requested': model,
    'key_present': bool(key),
    'model_list_status': 'NOT_RUN',
    'requested_model_listed': None,
    'generate_status': 'NOT_RUN',
    'generated_text_saved': False,
    'publishes_to_x': False,
}
if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}', model):
    result['generate_status'] = 'INVALID_MODEL_NAME'
elif not key:
    result['generate_status'] = 'MISSING_SECRET'
else:
    status, doc = request(BASE + '/models?pageSize=100', key)
    result['model_list_status'] = status
    if status == 200 and isinstance(doc, dict):
        eligible = [x.get('name', '').removeprefix('models/') for x in doc.get('models', [])
                    if 'generateContent' in x.get('supportedGenerationMethods', [])]
        result['generate_content_models'] = sorted(eligible)[:100]
        result['requested_model_listed'] = model in eligible
        result['model_list_has_next_page'] = bool(doc.get('nextPageToken'))
    # Send only one very small request; do not retry or run the chain.
    payload = {'contents': [{'parts': [{'text': '日本語で「接続確認」とだけ返してください。'}]}],
               'generationConfig': {'maxOutputTokens': 32}}
    status, doc = request(BASE + '/models/' + urllib.parse.quote(model, safe='') + ':generateContent', key,
                          json.dumps(payload, ensure_ascii=False).encode('utf-8'))
    result['generate_status'] = status
    if status == 200:
        result['contains_candidates'] = bool(isinstance(doc, dict) and doc.get('candidates'))
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Gemini diagnostic summary (no secret or generated content):')
for k in ('model_requested', 'key_present', 'model_list_status', 'requested_model_listed', 'generate_status'):
    print(f'  {k}: {result[k]}')
print('Saved diagnostic_result.json')
