import json, time
from pathlib import Path
import joblib, pandas as pd

ROOT=Path(__file__).resolve().parents[2]; MODEL_PATH=ROOT/'models'/'flood_risk_model.joblib'
class ModelService:
 def __init__(self): self.model=None; self.reload()
 def reload(self):
  self.model=joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
 def predict(self, payload):
  if self.model is None: raise FileNotFoundError('Model not found. Run: python scripts/train_model.py')
  return self.predict_dict(payload.model_dump())
 def predict_dict(self, d):
  if self.model is None: raise FileNotFoundError('Model not found. Run: python scripts/train_model.py')
  d=dict(d); d.pop('soil_moisture',None); frame=pd.DataFrame([d])
  mapping={'rainfall_mm':'Rainfall_mm','temperature_c':'Temperature_C','humidity_pct':'Humidity_pct','river_discharge_m3_s':'River_Discharge_m3_s','water_level_m':'Water_Level_m','elevation_m':'Elevation_m','land_cover':'Land_Cover','soil_type':'Soil_Type','population_density':'Population_Density','infrastructure':'Infrastructure','historical_floods':'Historical_Floods'}
  frame=frame.rename(columns=mapping); frame['Latitude']=30.8; frame['Longitude']=78.0
  return float(self.model.predict_proba(frame)[:,1][0])
 def predict_timed(self, d):
  started=time.perf_counter(); probability=self.predict_dict(d)
  return probability, round((time.perf_counter()-started)*1000,2)
 def artifact(self,name,default):
  p=ROOT/'models'/name
  return json.loads(p.read_text()) if p.exists() else default
