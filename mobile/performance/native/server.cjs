const http = require('http');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../../..');
const ts = require(path.join(root, 'mobile/node_modules/typescript'));
require.extensions['.ts'] = (module, file) => module._compile(ts.transpileModule(fs.readFileSync(file,'utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,file);
const { activePlan } = require(path.join(root,'mobile/src/features/planning/planning.test-fixtures.ts'));
const { savedCheckIn } = require(path.join(root,'mobile/src/features/checkins/checkIn.test-fixtures.ts'));
const now = () => new Date().toISOString();
const athlete = '00000000-0000-4000-8000-000000000001';
const token = () => ['eyJhbGciOiJIUzI1NiJ9', Buffer.from(JSON.stringify({sub:athlete,exp:Math.floor(Date.now()/1000)+86400,role:'authenticated'})).toString('base64url'), 'synthetic'].join('.');
const onboarding = {status:'completed',current_step:'completed', completed_steps:[],current_onboarding_version:'phase-14-onboarding-v2',current_ruleset_version:'phase-13-joren-ruleset-1',completed_onboarding_version:'phase-14-onboarding-v2',completed_ruleset_version:'phase-13-joren-ruleset-1',upgrade_required:false,missing_upgrade_steps:[], profile:{athlete_id:athlete,first_name:'Synthetic',last_name:'Benchmark',date_of_birth:'1990-05-20',resting_heart_rate_bpm:52,timezone:'Europe/Amsterdam',timezone_source:'manual',timezone_confirmed_at:now(),heart_rate_monitor_confirmed_at:now(),onboarding_status:'completed',revision:4,identifying_revision:2,physiology_revision:2,created_at:now(),updated_at:now()},training_history:[],primary_goal:null,required_disciplines:['run'],zones:[],discipline_setups:[],can_complete:true,initial_plan_request_id:'00000000-0000-4000-8000-000000000002',onboarding_revision:4};
const today = new Date(); const monday = new Date(today); monday.setDate(today.getDate()-(today.getDay()+6)%7); const iso = date => date.toISOString().slice(0,10);
activePlan.week_start = iso(monday); activePlan.available_dates = [0,2,5].map(day=>iso(new Date(+monday+day*86400000)));
activePlan.workouts = activePlan.workouts.map(workout=>({...workout,scheduled_date:activePlan.available_dates[1]}));
const rows=[];
const server = http.createServer((req,res)=>{
  const url = new URL(req.url,'http://localhost'); const route=url.pathname;
  if(route==='/__metrics') {res.writeHead(200,{'content-type':'application/json'});res.end(JSON.stringify(rows));return;}
  if(route==='/__reset') {rows.length=0;res.end('{}');return;}
  let status=200, body, delay=40;
  if(route==='/auth/v1/token') body={access_token:token(),refresh_token:'synthetic-local-refresh',token_type:'bearer',expires_in:86400,user:{id:athlete,aud:'authenticated',role:'authenticated',email:'synthetic@example.invalid',app_metadata:{provider:'email'},user_metadata:{},created_at:now()}};
  else if(route==='/api/v1/onboarding') body=onboarding;
  else if(route==='/api/v1/onboarding/goal-options') {body=[];delay=240;}
  else if(route==='/api/v1/me/physiology-profile') {body={date_of_birth:'1990-05-20',resting_heart_rate_bpm:52,revision:2};delay=240;}
  else if(route==='/api/v1/weekly-plans/recovery') body={active:activePlan,pending:null,draft:null};
  else if(route==='/api/v1/calendar') body={from_date:url.searchParams.get('from'),to_date:url.searchParams.get('to'),workouts:activePlan.workouts,rest_days:[]};
  else if(route.startsWith('/api/v1/weekly-plans/')) body=activePlan;
  else if(route==='/api/v1/activities'||route==='/api/v1/activities/pending-rpe'||route.includes('planned-external-activities')||route.includes('injury-restrictions')) body=[];
  else if(route.includes('calibration/status')) body={setups:[],evaluations:[],threshold_decisions:[]};
  else if(route.includes('zone-profile')) body={disciplines:[]};
  else if(route.includes('polar/connection')) body=null;
  else if(route==='/api/v1/checkins') body=savedCheckIn;
  else {status=404;body={error:{code:'synthetic_not_found',message:'Synthetic fixture unavailable'}};}
  const entry={route:route.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/g,':id'),method:req.method,status,started:performance.now(),delay}; rows.push(entry);
  req.resume(); setTimeout(()=>{res.writeHead(status,{'content-type':'application/json'});res.end(JSON.stringify(body));entry.completed=performance.now();},delay);
});
server.listen(18749,'127.0.0.1',()=>console.log('Synthetic local benchmark server ready'));
