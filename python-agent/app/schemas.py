from pydantic import BaseModel,Field
class TaskCreate(BaseModel):
    issue:str=Field(min_length=3,max_length=20000)
    repository:str=Field(min_length=1,max_length=200)
class RunRequest(BaseModel):
    approval_token:str|None=None
