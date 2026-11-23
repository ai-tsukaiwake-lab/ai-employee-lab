"""AI社員管理室: 制作AI（下書きのみ、X接続なし）。"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not key:
        sys.exit('Missing GEMINI_API_KEY secret. No request sent.')
    model = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    topic = os.environ.get('TOPIC', 'ChatGPTとGeminiの使い分け').strip()
    if not model or '/' in model or '?' in model or '#' in model:
        sys.exit('Invalid GEMINI_MODEL')
    if len(topic) > 200:
        sys.exit('TOPIC is too long')

    prompt = f'''あなたは「AI使い分け研究所」の制作AIです。対象は実験専用Xアカウント @FX_Civilservant の投稿下書きのみです。
テーマ: {topic}
目的: AI初心者が「どんな状況でどちらを使うか」を判断するための検証企画をわかりやすく伝える。

重要な事実関係:
- 企画AIは、長文要約・数値表の整形・アイデア出しの比較を提案した。
- 調査AIは、これらについて検証計画を作ったがWeb確認・出典検証・実測比較は未実施。
- 企画AIと調査AIのJSONをこの実行で自動取得したわけではない。上記は事前に人間が確認した要約。

日本語で次の内容を作成してください:
1. X投稿の下書きを3案。実験予告／検証手順の共有／読者への質問をそれぞれ1案。
2. 各案に「タイトル」「想定読者の悩み」「投稿本文（日本語140字以内を目標）」「添付画像案」「公開前の要確認事項」を含める。
3. 最後に「人間の承認前チェックリスト」を付ける。

絶対条件:
- 検証していない性能の優劣、処理時間、価格、最新機能、数値・実績は断定しない。
- 実施した実験と今後予定している実験を混同しない。
- 架空の出典や実測値、引用を作らない。
- 金融・公務員の話題に偏らず一般利用者向けにする。
- 投稿は実行しない。文章作成だけ。
- 各案は絵文字0〜1個、煽りや過剰な断定を避ける。'''
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.35},
    }
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key},
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        # APIキーなどの機密情報をログに表示しない
        sys.exit(f'Gemini API request failed: HTTP {error.code}')
    except Exception as error:
        sys.exit(f'Gemini API request failed: {type(error).__name__}')

    parts = [part.get('text', '')
             for candidate in data.get('candidates', [])
             for part in candidate.get('content', {}).get('parts', [])]
    result = '\n'.join(parts).strip()
    if not result:
        sys.exit('Gemini returned no text; no artifact generated')

    document = {
        'status': 'DRAFT_UNVERIFIED',
        'role': '制作AI',
        'topic': topic,
        'model': model,
        'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'input_source': 'PROMPT_SUMMARY_ONLY',
        'previous_artifacts_auto_loaded': False,
        'external_web_checked': False,
        'comparison_test_completed': False,
        'human_approved': False,
        'x_posted': False,
        'result': result,
    }
    with open('creation_result.json', 'w', encoding='utf-8') as file:
        json.dump(document, file, ensure_ascii=False, indent=2)
    print('Creation AI draft generated and saved to creation_result.json. No X actions were performed.')


if __name__ == '__main__':
    main()
