from app.schemas import TaskCreate
def test_task_contract():
    t=TaskCreate(issue="Fix refund validation",repository="demo-java")
    assert t.repository=="demo-java"
