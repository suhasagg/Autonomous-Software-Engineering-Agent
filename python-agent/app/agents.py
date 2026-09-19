from pydantic import BaseModel,Field
from agents import Agent,Runner
from agents.mcp import MCPServerStreamableHttp
from .config import settings

class Plan(BaseModel):
    summary:str
    files_to_inspect:list[str]=Field(default_factory=list)
    implementation_steps:list[str]
    tests:list[str]
    risks:list[str]=Field(default_factory=list)

class Review(BaseModel):
    approved:bool
    issues:list[str]=Field(default_factory=list)
    summary:str

explorer=Agent(
 name="Repository Explorer",model=settings.openai_model,
 instructions="Use read-only repository tools. Understand architecture, relevant files, tests and conventions. Do not edit.")

planner=Agent(
 name="Software Engineering Planner",model=settings.openai_model,output_type=Plan,
 instructions="Produce a minimal implementation plan from the issue and repository evidence. Avoid speculative rewrites.")

reviewer=Agent(
 name="Senior Code Reviewer",model=settings.openai_model,output_type=Review,
 instructions="Review diff and test output for correctness, security, regressions, maintainability and issue coverage.")

async def run_task(task_id,issue,approval_token,mcp_url,max_loops):
    headers={"X-Task-Id":task_id}
    if approval_token: headers["X-Approval-Token"]=approval_token
    async with MCPServerStreamableHttp(
      name="coding-workspace",
      params={"url":mcp_url,"headers":headers,"timeout":30},
      cache_tools_list=True,max_retry_attempts=2
    ) as mcp:
        explore=Agent(
          name=explorer.name,model=settings.openai_model,instructions=explorer.instructions,mcp_servers=[mcp])
        evidence=(await Runner.run(explore,
          f"Task {task_id}. Explore the repository for this issue:\n{issue}\nUse repo_tree, search_code and read_file.")).final_output

        plan=(await Runner.run(planner,
          f"Issue:\n{issue}\n\nRepository evidence:\n{evidence}")).final_output

        coder=Agent(
          name="Coding Agent",model=settings.openai_model,mcp_servers=[mcp],
          instructions=(
            "Implement the approved plan with the smallest coherent patch. "
            "Use read_file before write_file. write_file requires the provided approval token. "
            "Never modify .git, secrets, generated binaries, or files outside workspace. "
            "After editing, call run_build and git_diff. Never claim tests passed unless run_build says so."
          ))

        prompt=f"Issue:\n{issue}\nPlan:\n{plan.model_dump_json()}\nApproval token: {approval_token or 'NONE'}"
        coding=str((await Runner.run(coder,prompt)).final_output)

        final_review=None
        for loop in range(max_loops+1):
            inspect=Agent(
              name="Review Evidence Collector",model=settings.openai_model,mcp_servers=[mcp],
              instructions="Call git_diff and run_build. Return exact evidence, including failures.")
            evidence2=str((await Runner.run(inspect,"Collect current diff and build/test evidence.")).final_output)
            final_review=(await Runner.run(reviewer,
              f"Issue:\n{issue}\nPlan:\n{plan.model_dump_json()}\nEvidence:\n{evidence2}")).final_output
            if final_review.approved or loop>=max_loops: break
            repair=Agent(
              name="Repair Agent",model=settings.openai_model,mcp_servers=[mcp],
              instructions="Fix only the review findings. Keep changes minimal. Use approval token for writes, then run build.")
            await Runner.run(repair,
              f"Issue:{issue}\nReview issues:{final_review.model_dump_json()}\nApproval token:{approval_token or 'NONE'}")

        pr=Agent(
          name="PR Writer",model=settings.openai_model,
          instructions="Write a concise PR-style summary: problem, changes, tests, risks, and reviewer status. Do not invent results.")
        summary=str((await Runner.run(pr,
          f"Issue:{issue}\nPlan:{plan.model_dump_json()}\nCoding:{coding}\nReview:{final_review.model_dump_json()}")).final_output)
        return {"exploration":str(evidence),"plan":plan.model_dump(),"coding":coding,
                "review":final_review.model_dump(),"pr_summary":summary}
