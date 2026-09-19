import json,os,httpx
base=os.getenv("AGENT_API","http://localhost:8000")
tools=os.getenv("TOOLS_API","http://localhost:8081")
cases=json.load(open("dataset.json"));passed=0
for c in cases:
 x=httpx.post(base+"/v1/tasks",json={"issue":c["issue"],"repository":"demo-java"},timeout=20).json()
 tid=x["task_id"]
 token=httpx.post(f"{tools}/api/approvals/{tid}",timeout=20).json()["approval_token"]
 r=httpx.post(f"{base}/v1/tasks/{tid}/run",json={"approval_token":token},timeout=300)
 r.raise_for_status();out=r.json()
 text=json.dumps(out)
 ok=out["status"] in {"COMPLETED","REVIEW_REQUIRED"} and all(t in text for t in c["expected"])
 print("PASS" if ok else "FAIL",c["id"],out["status"]);passed+=int(ok)
print(f"{passed}/{len(cases)} passed")
raise SystemExit(0 if passed==len(cases) else 1)
