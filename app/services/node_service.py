from datetime import datetime, timezone

def _node(id, name, lat, lon, **data): return {"node_id":id,"location_name":name,"latitude":lat,"longitude":lon,"last_seen":datetime.now(timezone.utc),**data}
NODES = [
 _node("NODE-01","Joshimath proposed high-altitude point",30.555,79.565,battery_percent=87,rssi=-70,sensor_health=95,online=True,rainfall=35,temperature=-2,soil_moisture=None,water_level=None,slope_motion=None,purpose="Monitor upstream environmental conditions and high-altitude accumulation.",sensors="Temperature · rainfall · pressure"),
 _node("NODE-02","Rudraprayag proposed catchment",30.27528,78.965,battery_percent=74,rssi=-77,sensor_health=91,online=True,rainfall=42,temperature=8,soil_moisture=61,water_level=None,slope_motion=None,purpose="Detect intense rainfall and soil saturation before downstream impact.",sensors="Rainfall · soil moisture · temperature"),
 _node("NODE-03","Srinagar proposed slope point",30.229,78.787,battery_percent=91,rssi=-68,sensor_health=93,online=True,rainfall=38,temperature=10,soil_moisture=58,water_level=None,slope_motion=.08,purpose="Detect terrain and slope-instability signals.",sensors="IMU/tilt · soil moisture · rainfall"),
 _node("NODE-04","Devprayag proposed river gauge",30.146,78.598,battery_percent=80,rssi=-74,sensor_health=97,online=True,rainfall=30,temperature=13,soil_moisture=None,water_level=2.3,slope_motion=None,purpose="Monitor Alaknanda/Bhagirathi river response before downstream impact.",sensors="Water level · discharge · rise rate"),
 _node("NODE-05","Rishikesh proposed village point",30.10321,78.304,battery_percent=68,rssi=-82,sensor_health=88,online=True,rainfall=27,temperature=15,soil_moisture=47,water_level=1.8,slope_motion=None,purpose="Provide localized downstream warning context.",sensors="Water level · rainfall · local environment")]
def public_nodes(): return [{**n,"last_seen":n["last_seen"].isoformat()} for n in NODES]
def toggle(node_id, online):
 for n in NODES:
  if n["node_id"]==node_id: n["online"],n["last_seen"]=online,datetime.now(timezone.utc); return n
 return None
def sync_telemetry(rainfall, water, soil, temp):
 for i,n in enumerate(NODES):
  if n["online"]:
   n["rainfall"],n["temperature"] = round(rainfall*(.75+.08*i),1),round(temp-5+i*2,1)
   if n["soil_moisture"] is not None: n["soil_moisture"]=round(soil*(.9+.03*i),1)
   if n["water_level"] is not None: n["water_level"]=round(water*(.85+.06*i),2)
   n["last_seen"]=datetime.now(timezone.utc)
