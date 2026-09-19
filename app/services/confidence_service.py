from datetime import datetime, timezone

WEIGHTS = {"node_health": .30, "freshness": .20, "battery": .15, "network": .15, "consistency": .20}

def calculate(nodes, rainfall, water_level, soil_moisture):
    online = [n for n in nodes if n["online"]]; total = len(nodes) or 1
    health = sum(n["sensor_health"] for n in online) / (100 * total)
    battery = sum(n["battery_percent"] for n in online) / (100 * total)
    network = len(online) / total
    now = datetime.now(timezone.utc)
    fresh = sum(max(0, 1 - (now - n["last_seen"]).total_seconds()/300) for n in online) / total
    rain_high, soil_high, water_high = rainfall >= 120, soil_moisture >= 70, water_level >= 5
    divergence = rain_high and not water_high; corroboration = sum([rain_high, soil_high, water_high]) >= 3
    consistency = .35 if divergence else (.98 if corroboration else .76)
    score = round(max(0, min(1, .30*health + .20*fresh + .15*battery + .15*network + .20*consistency))*100, 1)
    return {"score":score, "label":"HIGH" if score>=75 else ("MEDIUM" if score>=50 else "LOW"), "network_status":"HEALTHY" if network>=.8 else ("DEGRADED" if network>=.5 else "CRITICAL"), "fusion_message":"Sensor divergence detected: upstream rainfall is elevated while river level remains normal." if divergence else ("Multi-node corroboration detected across rainfall, soil saturation and river level." if corroboration else "Telemetry chain is being monitored for corroboration.")}
