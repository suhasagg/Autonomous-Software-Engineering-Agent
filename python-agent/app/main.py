import uuid,time
from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter,Histogram,make_asgi_app
from .database import init_db,get_db
from .models import CodingTask,AuditEvent
from .schemas import TaskCreate,RunRequest
from .agents import run_task
from .config import settings

REQ=Counter("coding_agent_requests_total","Coding agent requests",["operation"])
LAT=Histogram("coding_agent_seconds","Coding task duration")
app=FastAPI(title="Autonomous Software Engineering Agent",version="1.0.0")
app.mount("/metrics",make_asgi_app())

@app.on_event("startup")
async def startup(): await init_db()

@app.get("/health")
async def health(): return {"status":"ok"}

@app.post("/v1/tasks")
async def create(req:TaskCreate,db:AsyncSession=Depends(get_db)):
    tid="TASK-"+uuid.uuid4().hex[:10]
    db.add(CodingTask(id=tid,repository=req.repository,issue=req.issue,status="AWAITING_APPROVAL"))
    db.add(AuditEvent(task_id=tid,event="CREATED",payload=req.model_dump()))
    await db.commit()
    return {"task_id":tid,"status":"AWAITING_APPROVAL"}

@app.post("/v1/tasks/{tid}/run")
async def run(tid:str,req:RunRequest,db:AsyncSession=Depends(get_db)):
    task=await db.get(CodingTask,tid)
    if not task: raise HTTPException(404,"task not found")
    REQ.labels("run").inc();start=time.perf_counter();task.status="RUNNING";await db.commit()
    try:
        result=await run_task(tid,task.issue,req.approval_token,settings.code_mcp_url,settings.max_repair_loops)
        task.result=result
        task.status="COMPLETED" if result["review"]["approved"] else "REVIEW_REQUIRED"
        db.add(AuditEvent(task_id=tid,event="FINISHED",payload={"status":task.status}))
        await db.commit()
        return {"task_id":tid,"status":task.status,"result":result}
    except Exception as e:
        task.status="FAILED";db.add(AuditEvent(task_id=tid,event="FAILED",payload={"error":str(e)[:1000]}))
        await db.commit();raise
    finally: LAT.observe(time.perf_counter()-start)

@app.get("/v1/tasks/{tid}")
async def get(tid:str,db:AsyncSession=Depends(get_db)):
    t=await db.get(CodingTask,tid)
    if not t: raise HTTPException(404,"task not found")
    return {"task_id":t.id,"repository":t.repository,"issue":t.issue,"status":t.status,"result":t.result}
