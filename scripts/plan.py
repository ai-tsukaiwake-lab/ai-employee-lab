import json, os, sys, urllib.request, urllib.error, datetime

key=os.environ.get('GEMINI_API_KEY','')
model=os.environ.get('GEMINI_MODEL','gemini-2.5-flash')
topic=os.environ.get('TOPIC','ChatGPTとGrok、X投稿の企画に向いているのはどっち？')
if not key:
    sys.exit('GEMINI_API_KEY is missing. No request sent.')
prompt=f'''あなたは「AI使い分け研究所」の企画AIです。実験用アカウント @FX_Civilservant の投稿企画だけを担当します。
テーマ: {topic}
読者の悩みを起点に、検証可能なX投稿企画を3案、日本語で作成してください。
各案に「タイトル」「読者の悩み」「検証方法」「必要な証拠」「注意点」を含めてください。
性能比較の優劣を実測なしに断定しないこと。これは企画案であり調査済みの事実ではありません。
Xへの投稿、外部サービス操作、承認は行いません。'''
payload={'contents':[{'parts':[{'text':prompt}]}], 'generationConfig':{'temperature':0.6}}
url='https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent'
req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
try:
    with urllib.request.urlopen(req,timeout=45) as resp:
        result=json.load(resp)
except urllib.error.HTTPError as e:
    print('AI API request failed with HTTP',e.code,file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print('AI API request failed:',type(e).__name__,file=sys.stderr)
    sys.exit(1)
parts=result.get('candidates',[{}])[0].get('content',{}).get('parts',[])
answer='\n'.join(p.get('text','') for p in parts if 'text' in p)
if not answer.strip():
    sys.exit('AI returned no text')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
with open('planner_result.json','w',encoding='utf-8') as f:
    json.dump({'status':'AI_EXECUTED','role':'企画AI','topic':topic,'model':model,'timestamp_utc':now,'result':answer,'x_posted':False,'human_approved':False},f,ensure_ascii=False,indent=2)
print('AI generated a draft successfully. No X actions were performed.')
