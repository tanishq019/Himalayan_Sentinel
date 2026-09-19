"""Single-authority, deterministic simulation state for Himalayan Sentinel."""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import random, threading, time
from . import node_service
from .confidence_service import calculate
from .alert_service import AlertService

MAX_HISTORY=120
SCENARIOS={"NORMAL":{"target":25,"fault":None},"MONSOON BUILDUP":{"target":80,"fault":None},"HEAVY RAIN":{"target":150,"fault":None},"UPSTREAM SURGE":{"target":190,"fault":None},"MULTI-NODE EVENT":{"target":240,"fault":None},"NODE FAILURE":{"target":180,"fault":"NODE-02"},"NETWORK DEGRADATION":{"target":110,"fault":"network"},"RECOVERY":{"target":15,"fault":None}}

class SimulationService:
 def __init__(self,model): self.model=model; self.lock=threading.RLock(); self.reset()
 def reset(self):
  with self.lock:
   self.rng=random.Random(42); self.running=True; self.scenario='NORMAL'; self.sim_time=0.; self.sequence=0; self.last=time.monotonic(); self.rain=28.; self.soil=42.; self.discharge=260.; self.water=2.; self.temp=13.; self.humidity=72.; self.slope=.05; self.rain_lag=deque([25.]*8,maxlen=8); self.history=deque(maxlen=MAX_HISTORY); self.event_stage=0; self.stage_times={}; self.fault=None; self.previous_level=None; self.demo=False; self.alerts=AlertService()
   for n in node_service.NODES: n.update(online=True,battery_percent=max(n['battery_percent'],65),sensor_health=max(n['sensor_health'],88),rssi=min(n['rssi'],-65))
   self._advance(2.)
 def set_scenario(self,name,clear_alerts=True):
  name=name.upper()
  if name not in SCENARIOS: raise ValueError('Unknown scenario')
  with self.lock:
   self.scenario,self.fault=name,SCENARIOS[name]['fault']
   if clear_alerts:self.alerts=AlertService()
   self.alerts.add('INFO','NETWORK',f'{name.title()} simulation phase activated.','scenario')
   if self.fault and self.fault.startswith('NODE'):node_service.toggle(self.fault,False)
   elif name=='RECOVERY': node_service.toggle('NODE-02',True)
   self._publish_snapshot()
 def start_demo(self):
  self.reset()
  with self.lock: self.demo=True; self.alerts.add('INFO','NETWORK','Deterministic demonstration started.','demo'); self._publish_snapshot()
 def _tick(self,force=False):
  with self.lock:
   now=time.monotonic(); elapsed=now-self.last
   if not force and (not self.running or elapsed<1.5):return False
   self.last=now; self._advance(2. if force else max(1.,elapsed)); return True
 def _advance(self,dt):
  if self.demo:
   plan=[(0,'NORMAL'),(14,'MONSOON BUILDUP'),(28,'HEAVY RAIN'),(42,'UPSTREAM SURGE'),(56,'MULTI-NODE EVENT'),(70,'NODE FAILURE'),(84,'RECOVERY')]
   phase=[p for at,p in plan if self.sim_time>=at][-1]
   if phase!=self.scenario:
    self.scenario,self.fault=phase,SCENARIOS[phase]['fault']; self.alerts.add('INFO','NETWORK',f'{phase.title()} demonstration phase activated.','demo-phase-'+phase)
    if self.fault and self.fault.startswith('NODE'):node_service.toggle(self.fault,False)
    elif phase=='RECOVERY':node_service.toggle('NODE-02',True)
  target=SCENARIOS[self.scenario]['target']; rate=.12 if self.scenario in ('MONSOON BUILDUP','RECOVERY') else .22
  self.rain=max(0,self.rain+(target-self.rain)*rate+self.rng.gauss(0,1.1)); self.rain_lag.append(self.rain); lag=sum(list(self.rain_lag)[:4])/4
  self.soil=max(15,min(99,self.soil+(min(96,28+self.rain*.34)-self.soil)*.11+self.rng.gauss(0,.35))); runoff=max(0,lag*(.8+self.soil/180)); self.discharge=max(50,self.discharge+(220+runoff*5-self.discharge)*.16+self.rng.gauss(0,6)); self.water=max(.4,self.water+(1.4+self.discharge/250-self.water)*.12+self.rng.gauss(0,.018)); self.temp+=(13-self.temp)*.04+self.rng.gauss(0,.06); self.humidity=max(20,min(100,60+self.rain*.17+self.rng.gauss(0,.5))); self.slope=max(.01,self.slope+(max(0,self.soil-65)*self.rain/12000-self.slope)*.12+self.rng.gauss(0,.005)); self.sim_time+=dt
  self.event_stage=4 if self.water>5 else 3 if self.water>3.6 else 2 if self.soil>64 else 1 if self.rain>65 else 0
  for stage in range(1,self.event_stage+1):self.stage_times.setdefault(str(stage),round(self.sim_time,1))
  self._update_nodes(); self._predict(); self._alerts(); self._publish_snapshot()
 def _update_nodes(self):
  for i,n in enumerate(node_service.NODES):
   if not n['online']:continue
   lead=[1.05,1.12,.98,.84,.72][i]; n['rainfall']=round(max(0,self.rain*lead+self.rng.gauss(0,.5)),1); n['temperature']=round(self.temp-5+i*2+self.rng.gauss(0,.1),1)
   if n['soil_moisture'] is not None:n['soil_moisture']=round(max(0,min(100,self.soil*(.92+.04*i)+self.rng.gauss(0,.25))),1)
   if n['water_level'] is not None:n['water_level']=round(max(0,self.water*(.82+.08*i)+self.rng.gauss(0,.015)),2)
   if n['slope_motion'] is not None:n['slope_motion']=round(max(0,self.slope+self.rng.gauss(0,.005)),3)
   n['battery_percent']=round(max(4,n['battery_percent']-.006),1); n['rssi']=round(-68-self.rng.random()*13-(10 if self.fault=='network' else 0),1); n['last_seen']=datetime.now(timezone.utc)
 def _predict(self):
  self.payload={'rainfall_mm':self.rain,'temperature_c':self.temp,'humidity_pct':self.humidity,'river_discharge_m3_s':self.discharge,'water_level_m':self.water,'elevation_m':1800,'land_cover':'Forest','soil_type':'Loam','population_density':120,'infrastructure':1,'historical_floods':1 if self.scenario!='NORMAL' else 0,'soil_moisture':self.soil}
  try:self.prob,self.latency_ms=self.model.predict_timed(self.payload)
  except Exception:self.prob,self.latency_ms=0.,0.
  self.prob=float(max(0,min(1,self.prob))); self.level='NORMAL' if self.prob<.25 else 'WATCH' if self.prob<.5 else 'WARNING' if self.prob<.75 else 'CRITICAL'; self.conf=calculate(node_service.NODES,self.rain,self.water,self.soil); self.conf['score']=float(max(0,min(100,self.conf['score'])))
 def _alerts(self):
  for active,severity,node,msg,key in [(self.rain>65,'INFO','NODE-02','Rainfall intensity increasing upstream.','rain'),(self.soil>65,'WATCH','NODE-03','Soil saturation increasing at slope monitoring node.','soil'),(self.water>3.6,'WARNING','NODE-04','River level rise detected at river gauge.','river'),(self.event_stage>=4,'CRITICAL','NODE-05','Downstream flood risk exceeds prototype warning threshold.','down')]:
   if active:self.alerts.add(severity,node,msg,key)
   else:self.alerts.clear_key(key)
  if self.previous_level is not None and self.level!=self.previous_level:self.alerts.add(self.level,'MODEL',f'Risk transitioned {self.previous_level} → {self.level}.','risk-transition-'+self.level)
  self.previous_level=self.level
  for n in node_service.NODES:
   key='node-offline-'+n['node_id']
   if not n['online']:self.alerts.add('WARNING',n['node_id'],'Node transmission stopped; coverage degraded.',key)
   else:self.alerts.clear_key(key)
 def _snapshot_data(self):
  old=self.history[max(0,len(self.history)-25)] if self.history else None; pct=round(self.prob*100,1); delta=round(pct-old['risk']['percentage'],1) if old else 0.; local=[self.level if self.event_stage>=threshold else 'NORMAL' for threshold in (1,1,2,3,4)]; nodes=node_service.public_nodes()
  for n,lvl in zip(nodes,local):n['local_risk_level']=lvl; n['local_risk']=round(self.prob if lvl==self.level else max(.05,self.prob-.2),4)
  return {'sequence_number':self.sequence,'timestamp':datetime.now(timezone.utc).isoformat(),'phase':self.scenario,'telemetry':{**{k:round(v,4) if isinstance(v,float) else v for k,v in self.payload.items()},'slope_motion':round(self.slope,3)},'risk':{'probability':round(self.prob,4),'percentage':pct,'level':self.level,'delta':delta,'trend':'RISING' if delta>1 else 'FALLING' if delta<-1 else 'STABLE','prediction_latency_ms':round(self.latency_ms,2)},'confidence':{'value':round(self.conf['score'],1),'level':self.conf['label'],'reason':self.conf['fusion_message']},'nodes':nodes,'event_chain':[{'stage':i+1,'name':name,'status':'ACTIVE' if self.event_stage>=i+1 else 'PENDING','activated_at':self.stage_times.get(str(i+1))} for i,name in enumerate(['UPSTREAM ANOMALY','SLOPE RESPONSE','RIVER RESPONSE','DOWNSTREAM ALERT'])],'alerts':self.alerts.public(),'network_status':self.conf['network_status'],'monitoring_mode':{'NORMAL':'LOW-FREQUENCY','WATCH':'INCREASED','WARNING':'HIGH-FREQUENCY','CRITICAL':'MAXIMUM / ALERT PRIORITY'}[self.level],'sample_interval':{'NORMAL':'30 sec','WATCH':'15 sec','WARNING':'5 sec','CRITICAL':'2 sec'}[self.level],'downstream_impact':[{'zone':z,'level':l} for z,l in zip(['Upstream catchment','Slope corridor','Devprayag river corridor','Rishikesh monitoring zone'],local)],'running':self.running,'simulation_time':round(self.sim_time,1)}
 def _publish_snapshot(self):
  self.sequence+=1; self.current=self._snapshot_data(); self.history.append(deepcopy(self.current)); self.validate_snapshot_consistency()
 def validate_snapshot_consistency(self):
  assert self.history and self.current['sequence_number']==self.history[-1]['sequence_number'] and self.current['timestamp']==self.history[-1]['timestamp']
  for key in ('telemetry','risk','confidence','nodes','event_chain','alerts'):assert self.current[key]==self.history[-1][key],f'Snapshot mismatch: {key}'
 def state(self):
  with self.lock:self.validate_snapshot_consistency(); return {'current_state':deepcopy(self.current),'history':deepcopy(list(self.history))}
 def get_history(self):return self.state()
