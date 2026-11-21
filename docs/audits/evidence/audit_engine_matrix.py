"""Bounded synthetic catalog/first-week matrix; never calls network or persistence."""
import json,re,subprocess,sys,time
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
CASES={
 'run_zero': ('run',('0','0','0'),True),
 'tri_zero': ('tri',('0','0','0'),True),
 'tri_one_sport_history': ('tri',('0','0','3'),True),
 'tri_balanced': ('tri',('2','5','3'),True),
 'duathlon': ('duo',('0','5','3'),True),
 'swim_history': ('swim',('2','0','0'),True),
 'run_no_days': ('run',('0','0','3'),False),
}
def worker(name):
 from app.modules.workouts.repository import parse_planning_catalog
 from app.modules.workouts.catalog import CURRENT_CATALOG,active_catalog,ZoneRequirement
 from app.modules.physiology.models import Discipline
 from app.modules.physiology.joren import starting_baseline
 from app.modules.planning.domain import build_weekly_plan,ZoneCapability,PlanningConstraintError
 sql=(ROOT/'supabase/migrations/20260903074359_add_source_catalog_training_options.sql').read_text(encoding='utf-8')
 source=json.loads(re.search(r'\$catalog\$(.*?)\$catalog\$::jsonb',sql,re.S).group(1))
 rows=[]
 for row in source:
  rows.append({**row,'version':2,'fallback_compatibility':'compatible','explicit_scheduling_only':False,
    'athlete_selection_only':False,'source_catalog':'start23-v0.1',
    'training_phases':['build'] if any(s.get('zone_number',0)>2 for s in row['segments']) else ['base','build','recovery','taper'],
    'zone_requirements':[], 'segments':[{**s,'is_swim_technique':False} for s in row['segments']]})
 catalog=active_catalog((*CURRENT_CATALOG,*parse_planning_catalog(tuple(rows))))
 goal,hours,available=CASES[name]
 sports=frozenset(Discipline) if goal=='tri' else frozenset({Discipline.BIKE,Discipline.RUN}) if goal=='duo' else frozenset({Discipline(goal)})
 baseline=starting_baseline({sport:Decimal(hour)*60 for sport,hour in zip(Discipline,hours)})
 start=date(2026,10,26)
 started=time.perf_counter()
 try:
  plan=build_weekly_plan(week_start=start,timezone_name='Europe/Amsterdam',race_date=date(2027,3,15),catalog=catalog,
    prior_loads=(),goal_disciplines=sports,confirmed_injuries=frozenset(),
    zone_capabilities={s:ZoneCapability(frozenset({ZoneRequirement.HEART_RATE,ZoneRequirement.PACE,ZoneRequirement.POWER})) for s in Discipline},
    available_dates=tuple(start+timedelta(days=i) for i in range(7)) if available else (),onboarding_baseline=baseline)
  result={'outcome':'generated_pending_input','workout_count':len(plan.workouts),'phase':plan.target.phase.value}
 except PlanningConstraintError as e: result={'outcome':'fail_closed','code':e.code}
 except Exception as e: result={'outcome':'unexpected_exception','type':type(e).__name__,'message':str(e)}
 result.update(case=name,seconds=round(time.perf_counter()-started,4))
 print(json.dumps(result))
if len(sys.argv)>1:
 worker(sys.argv[1])
else:
 results=[]
 for name in CASES:
  try:
   p=subprocess.run([sys.executable,__file__,name],capture_output=True,text=True,timeout=20)
   row=json.loads(p.stdout) if p.returncode==0 else {'case':name,'outcome':'worker_error','detail':p.stderr[-500:]}
  except subprocess.TimeoutExpired: row={'case':name,'outcome':'exceeded_20_second_audit_budget'}
  print(json.dumps(row),flush=True); results.append(row)
 Path(__file__).with_name('engine-matrix-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
