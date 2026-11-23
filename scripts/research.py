"""Research-planning AI for the experimental AI employee lab.
This script does NOT browse or verify external sources and does NOT post to X.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

key = os.environ.get('GEMINI_API_KEY', '')
model = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')
topic = os.environ.get('TOPIC', 'ChatGPTとGeminiの使い分け')
if not key:
    sys.exit('GEMINI_API_KEY is missing. No request sent.')

prompt = f'''あなたは「AI使い分け研究所」の調査設計AIです。対象は実験用Xアカウント @FX_Civilservant のみです。
テーマ：{topic}

目的：X投稿企画を根拠に基づいて検証するための「調査計画」を日本語で作ること。
外部Webの閲覧、検索、出典の検証を実施していない前提です。実在のURLや研究結果、最新価格、モデル性能を捏造しないでください。
この処理は調査そのものではなく調査準備です。調査済み、事実確認済み、比較実証済みという表現は使わないでください。
次の構成で回答してください。
1. 読者の困りごとと投稿の狙い
2. 検証すべき具体的な問いを3件
3. 一次情報として確認すべき資料の種類（例：各社公式ドキュメント）
4. 両AIに同条件で与えるプロンプトと、測定項目
5. 人間が実際に調べて記録すべきチェックリスト
6. 確認できるまで断定してはいけない事項
7. 次工程（制作AI）へ渡す情報と未確認事項
この企画だけでX投稿を作成・公開しないでください。'''

payload = {
    'contents': [{'parts': [{'text': prompt}]}],
    'generationConfig': {'temperature': 0.2},
}
url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
req = urllib.request.Request(
    url,
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    headers={'Content-Type': 'application/json', 'x-goog-api-key': key},
    method='POST',
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.load(resp)
except urllib.error.HTTPError as exc:
    # Do not dump response bodies: they can contain request details.
    sys.exit(f'Gemini API returned HTTP {exc.code}. Check model access and quota.')
except (urllib.error.URLError, TimeoutError) as exc:
    sys.exit(f'Gemini API network error: {type(exc).__name__}')

texts = []
for candidate in result.get('candidates', []):
    for part in candidate.get('content', {}).get('parts', []):
        if isinstance(part.get('text'), str):
            texts.append(part['text'])
answer = '\n'.join(texts).strip()
if not answer:
    sys.exit('Gemini returned no text. No artifact generated.')

output = {
    'status': 'RESEARCH_PLAN_ONLY',
    'role': '調査AI',
    'topic': topic,
    'model': model,
    'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'external_web_checked': False,
    'sources_verified': False,
    'human_approved': False,
    'x_posted': False,
    'result': answer,
}
with open('research_result.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print('Research plan saved to research_result.json. No web verification or X action performed.')
