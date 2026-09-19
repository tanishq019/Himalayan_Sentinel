import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .schemas import PredictionInput, PredictionResponse, NodeToggle
from .services.model_service import ModelService
from .services.simulation_service import SimulationService
from .services import node_service

app=FastAPI(title='Himalayan Sentinel'); app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
service=ModelService(); simulation=SimulationService(service)
@app.on_event('startup')
async def simulation_clock():
 async def clock():
  while True: simulation._tick(); await asyncio.sleep(2)
 asyncio.create_task(clock())
@app.get('/health')
def health(): return {'status':'ok','model_loaded':service.model is not None,'model_name':'RandomForestClassifier','simulation':'running' if simulation.running else 'paused'}
@app.post('/predict',response_model=PredictionResponse)
def predict(payload:PredictionInput):
 try: probability,latency=service.predict_timed(payload.model_dump())
 except FileNotFoundError as exc: raise HTTPException(503,str(exc))
 s=simulation.state()['current_state']; level='NORMAL' if probability<.25 else 'WATCH' if probability<.5 else 'WARNING' if probability<.75 else 'CRITICAL'; features=service.artifact('feature_importance.json',[])[:8]
 return {'risk_probability':round(probability,4),'risk_level':level,'system_confidence':s['confidence']['value'],'confidence_label':s['confidence']['level'],'contributors':features,'feature_contributions':features,'model_decision':'ELEVATED FLOOD RISK','prediction_latency_ms':latency,'nodes':s['nodes'],'network_status':s['network_status'],'fusion_message':s['confidence']['reason'],'monitoring_mode':s['monitoring_mode']}
@app.get('/metrics')
def metrics(): return service.artifact('metrics.json',{'detail':'No trained model metrics found.'})
@app.get('/feature-importance')
def fi(): return service.artifact('feature_importance.json',[])
@app.get('/api/simulation/state')
def state(): return simulation.state()
@app.get('/api/simulation/history')
def history(): return simulation.get_history()
@app.post('/api/simulation/start')
def start(): simulation.running=True; return simulation.state()
@app.post('/api/simulation/pause')
def pause(): simulation.running=False; return simulation.state()
@app.post('/api/simulation/reset')
def reset(): simulation.reset(); return simulation.state()
@app.post('/api/simulation/demo')
def demo(): simulation.start_demo(); return simulation.state()
@app.post('/api/simulation/scenario')
def scenario(body:dict):
 try: simulation.set_scenario(body.get('scenario','')); return simulation.state()
 except ValueError as exc: raise HTTPException(422,str(exc))
@app.get('/api/nodes')
@app.get('/nodes')
def nodes(): return simulation.state()['current_state']['nodes']
@app.get('/api/alerts')
def alerts(): return simulation.state()['current_state']['alerts']
@app.post('/api/nodes/{node_id}/toggle')
@app.post('/nodes/{node_id}/toggle')
def node_toggle(node_id:str,body:NodeToggle):
 n=node_service.toggle(node_id,body.online)
 if n is None: raise HTTPException(404,'Unknown node')
 simulation._tick(force=True); return simulation.state()['current_state']
@app.websocket('/ws/live')
async def live(ws:WebSocket):
 await ws.accept()
 try:
  while True: await ws.send_json(simulation.state()); await asyncio.sleep(2)
 except (WebSocketDisconnect,RuntimeError): pass
FRONTEND=Path(__file__).resolve().parents[1]/'frontend'; app.mount('/',StaticFiles(directory=FRONTEND,html=True),name='frontend')
