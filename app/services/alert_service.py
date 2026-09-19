from datetime import datetime, timezone

class AlertService:
    def __init__(self): self.items=[]; self.last={}
    def add(self, severity, node, message, key=None):
        key=key or message
        if self.last.get(key)==message: return
        self.last[key]=message
        self.items.insert(0,{"timestamp":datetime.now(timezone.utc).isoformat(),"severity":severity,"node":node,"message":message})
        self.items=self.items[:40]
    def clear_key(self,key): self.last.pop(key,None)
    def public(self): return self.items[:20]
