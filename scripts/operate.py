"""AI employee operations planner: advisory-only and no external actions.

This initial version does not read historical artifacts or access X.
It creates a demonstrative operations checklist from explicitly supplied
metadata, never asserts that upstream work has actually completed.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not api_key:
        sys.exit('GEMINI_API_KEY is missing. No request sent.')
    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash').strip()
    case_title = os.environ.get('CASE_TITLE', 'ChatGPTとGeminiの使い分け').strip()[:150]
    if not model or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-' for c in model):
        sys.exit('Invalid model name')

    prompt = f'''あなたは「AI使い分け研究所」の運用AIです。対象は実験用Xアカウント @FX_Civilservant のみです。
案件テーマ：{case_title}
これは動作確認用です。企画AI、調査AI、制作AI、監査AIのJSON成果物は一切渡されていません。
推測で「完了」「監査済み」「承認済み」「投稿済み」などと認定してはいけません。
日本語で次の見出しで作業管理案を作成してください：
1. 段階別の確認事項（企画、調査、制作、監査、運用、分析）
2. 現時点で実際には確認できない情報
3. 人間の承認を要する作業
4. 次の推奨手順（最大5件）
5. 誤操作・外部公開の安全上の注意
全ステータスは未確認として扱い、提案と事実を厳密に区別してください。
外部Web調査・X接続・投稿・承認は実施しません。'''
    payload = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0.2}}
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            response = json.load(res)
    except urllib.error.HTTPError as exc:
        print(f'Gemini API error HTTP {exc.code}', file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print('Gemini API request failed:', type(exc).__name__, file=sys.stderr)
        sys.exit(1)

    candidates = response.get('candidates', [])
    if not candidates:
        sys.exit('Gemini returned no candidates')
    parts = candidates[0].get('content', {}).get('parts', [])
    answer = '\n'.join(p.get('text', '') for p in parts if isinstance(p, dict) and 'text' in p)
    if not answer.strip():
        sys.exit('Gemini returned no text')

    result = {
        'status': 'OPERATIONS_PLAN_ONLY',
        'role': '運用AI',
        'account_scope': '@FX_Civilservant',
        'topic': case_title,
        'model': model,
        'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'input_source': 'CASE_TITLE_ONLY',
        'previous_artifacts_auto_loaded': False,
        'upstream_status_verified': False,
        'external_web_checked': False,
        'human_approved': False,
        'x_connected': False,
        'x_posted': False,
        'draft_status': 'UNVERIFIED',
        'result': answer,
        'notes': '動作確認の運用提案です。実際の案件進捗・承認・投稿は確認していません。',
    }
    with open('operations_result.json', 'w', encoding='utf-8') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
    print('Operations plan saved to operations_result.json. No X actions performed.')


if __name__ == '__main__':
    main()
