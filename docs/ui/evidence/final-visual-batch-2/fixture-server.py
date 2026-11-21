"""Loopback-only native public fixture service. Rejects all writes. Never records headers or bodies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
HERE=Path(__file__).parent
fixtures=json.loads((HERE/'public-fixtures.json').read_text(encoding='utf-8'))
onboarding={ 'status':'in_progress','current_step':'profile','completed_steps':[],
 'current_onboarding_version':'phase-14-onboarding-v2','current_ruleset_version':'phase-13-joren-ruleset-1',
 'completed_onboarding_version':None,'completed_ruleset_version':None,'upgrade_required':False,'missing_upgrade_steps':[],
 'profile':None,'training_history':[],'primary_goal':None,'required_disciplines':['run'],'zones':[],'discipline_setups':[],
 'can_complete':False,'initial_plan_request_id':None,'onboarding_revision':0 }
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def response(self,status,body):
  data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  url=urlparse(self.path);q=parse_qs(url.query);config=json.loads((HERE/'fixture-config.json').read_text())
  path=url.path;status=200
  if path=='/config': body=config
  elif path=='/api/v1/onboarding': body={**onboarding,**({} if config['gate'] else {'status':'completed','current_step':'completed','profile':{'timezone':'Europe/Amsterdam','timezone_confirmed_at':'2026-09-01T00:00:00Z'}})}
  elif path.startswith('/api/v1/weekly-plans/'):body=fixtures['activePlan']
  elif path=='/api/v1/calendar':body={'from_date':q.get('from_date',['2026-10-05'])[0],'to_date':q.get('to_date',['2026-10-12'])[0],'workouts':[fixtures['workout']],'rest_days':[]}
  elif path in ['/api/v1/activities','/api/v1/activities/pending-rpe']:body=[fixtures['pendingActivity']] if config['pending'] else []
  elif path=='/api/v1/planned-external-activities':body=[]
  elif path=='/api/v1/me/physiology-profile':body=None
  elif path=='/api/v1/onboarding/goal-options':body=[]
  else:status=404;body={'error':{'code':'review_read_not_available','message':'Public review fixture: unavailable read'}}
  with (HERE/'fixture-request-ledger.jsonl').open('a') as f:f.write(json.dumps({'method':'GET','path':path,'status':status,'config':config})+'\n')
  self.response(status,body)
 def reject(self):
  with (HERE/'fixture-request-ledger.jsonl').open('a') as f:f.write(json.dumps({'method':self.command,'path':urlparse(self.path).path,'status':405})+'\n')
  self.response(405,{'error':{'code':'review_write_disabled','message':'Public review fixture: writes disabled'}})
 do_POST=reject;do_PUT=reject;do_PATCH=reject;do_DELETE=reject
ThreadingHTTPServer(('127.0.0.1',8123),Handler).serve_forever()
