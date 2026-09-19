from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    openai_api_key:str
    openai_model:str="gpt-5.4"
    database_url:str="postgresql+asyncpg://coder:coder@localhost:5432/coder"
    redis_url:str="redis://localhost:6379/0"
    code_mcp_url:str="http://localhost:8081/mcp"
    max_repair_loops:int=2
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
