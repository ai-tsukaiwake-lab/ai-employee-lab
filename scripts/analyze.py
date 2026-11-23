"""AI Employee Lab: manual-metrics analysis, no X connectivity or posting.

GitHub Actions inputs are never assumed to be verified external measurements.
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

OUTPUT = 'analysis_result.json'
ALLOWED_METRICS = ('impressions', 'likes', 'replies', 'reposts', 'bookmarks', 'profile_visits', 'follows', 'link_clicks')


def save(payload):
    with open(OUTPUT, 'w', encoding='utf-8') as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    print(f'Saved {OUTPUT}; status={payload["status"]}; no X actions performed.')


def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    case_title = os.environ.get('CASE_TITLE', 'ChatGPTとGeminiの使い分け').strip()
    raw = os.environ.get('METRICS_JSON', '').strip()
    payload = {
        'role': '分析AI', 'account_scope': '@FX_Civilservant',
        'topic': case_title, 'timestamp_utc': now,
        'input_source': 'MANUAL_USER_ENTRY_UNVERIFIED',
        'x_connected': False, 'x_posted': False,
        'human_approved': False, 'external_web_checked': False,
        'metrics_verified_externally': False,
        'previous_artifacts_auto_loaded': False,
        'metrics': [], 'missing_metrics': [], 'analysis': None,
    }
    if not raw:
        payload['status'] = 'NEEDS_METRICS'
        payload['next_action'] = '投稿別の実測値をJSONで手入力してください。未取得値は省略またはnullとし、0とは区別してください。'
        save(payload)
        return
    try:
        data = json.loads(raw)
        if not isinstance(data, list) or not data:
            raise ValueError('Metrics must be a non-empty JSON array.')
        cleaned = []
        measured_count = 0
        missing = []
        for idx, record in enumerate(data):
            if not isinstance(record, dict):
                raise ValueError(f'Entry {idx + 1} must be a JSON object.')
            item = {'post_id': str(record.get('post_id', f'投稿{idx+1}'))[:100]}
            for key in ALLOWED_METRICS:
                value = record.get(key, None)
                if value is None:
                    item[key] = None
                    missing.append({'post_id': item['post_id'], 'field': key})
                elif type(value) is int and value >= 0:
                    item[key] = value
                    measured_count += 1
                else:
                    raise ValueError(f'Entry {idx+1}: {key} must be a nonnegative integer or null.')
            cleaned.append(item)
        if not measured_count:
            raise ValueError('At least one observed metric must be provided; all-null data is not enough.')
        payload['metrics'] = cleaned
        payload['missing_metrics'] = missing
    except (ValueError, json.JSONDecodeError) as exc:
        payload['status'] = 'INVALID_INPUT'
        payload['error'] = str(exc)
        save(payload)
        return

    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    model = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    payload['model'] = model
    if not api_key:
        payload['status'] = 'NEEDS_API_KEY'
        payload['next_action'] = 'GitHub Actionsのrepository secret GEMINI_API_KEYを設定してください。'
        save(payload)
        return

    instruction = (
        'あなたは「AI使い分け研究所」の分析AI。実験用アカウント@FX_Civilservantのみを対象とする。'
        '以下は人間が手入力した未検証の投稿指標。数字を一切補完・捏造せず、nullは未確認として扱い0と混同しない。'
        '観測された数値と仮説を明確に分け、投稿別比較は比較可能な指標だけで行う。'
        '分母が不明な率を計算せず、根拠のない原因の断定も避ける。'
        '日本語で「観測事実」「比較可能な範囲」「限界・未確認」「次の検証案（最大3件）」を出力する。'
        'X API操作、投稿、承認は行わない。\n'
        f'案件: {case_title}\n未検証の手入力データ:\n{json.dumps(payload["metrics"], ensure_ascii=False)}'
    )
    api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    body = json.dumps({'contents': [{'parts': [{'text': instruction}]}],
                       'generationConfig': {'temperature': 0.2}}).encode('utf-8')
    for attempt in range(3):
        req = urllib.request.Request(
            api_url, data=body,
            headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
            method='POST')
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                response_data = json.load(response)
            candidates = response_data.get('candidates') or []
            parts = candidates[0].get('content', {}).get('parts', []) if candidates else []
            answer = '\n'.join(p.get('text', '') for p in parts if 'text' in p).strip()
            if not answer:
                raise RuntimeError('Gemini did not return text.')
            payload['analysis'] = answer
            payload['status'] = 'ANALYSIS_DRAFT_UNVERIFIED'
            payload['notes'] = 'AIによる参考分析。手入力値の真偽は未検証。人間の確認・承認が必要。'
            save(payload)
            return
        except urllib.error.HTTPError as exc:
            print(f'Gemini API HTTP {exc.code} (attempt {attempt+1}/3)', file=sys.stderr)
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            payload['status'] = 'API_ERROR'
            payload['error'] = f'Gemini API HTTP {exc.code}'
            save(payload)
            sys.exit(1)
        except Exception as exc:
            payload['status'] = 'API_ERROR'
            payload['error'] = type(exc).__name__
            save(payload)
            sys.exit(1)


if __name__ == '__main__':
    main()
