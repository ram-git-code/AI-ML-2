import pytest

def test_quiz_generate_and_security(client):
    # 1. Generate quiz on Rajasthan GK
    res = client.post("/api/quizzes/generate", json={
        "query": "Give me 3 questions on Rajasthan GK",
        "number_of_questions": 3
    })
    assert res.status_code == 201
    quiz = res.json()
    assert "id" in quiz
    assert quiz["total_questions"] >= 1
    assert len(quiz["questions"]) >= 1

    # Security check: correct_answer and explanation MUST NOT be in public quiz payload
    first_q = quiz["questions"][0]
    assert "correct_answer" not in first_q
    assert "explanation" not in first_q
    assert "options" in first_q
    assert "question_text" in first_q

def test_quiz_answer_evaluation_lifecycle(client):
    # Generate quiz
    gen_res = client.post("/api/quizzes/generate", json={
        "query": "Physics questions",
        "number_of_questions": 2
    })
    assert gen_res.status_code == 201
    quiz = gen_res.json()
    quiz_id = quiz["id"]
    q1 = quiz["questions"][0]
    q1_id = q1["id"]

    # Submit an answer to q1
    ans_res = client.post(f"/api/quizzes/{quiz_id}/answers", json={
        "question_id": q1_id,
        "selected_answer": q1["options"][0] if q1["options"] else "A"
    })
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert "is_correct" in ans_data
    assert "correct_answer" in ans_data
    assert "explanation" in ans_data
    assert ans_data["total_answered"] >= 1

    # Check summary
    summary_res = client.get(f"/api/quizzes/{quiz_id}/summary")
    assert summary_res.status_code == 200
    assert summary_res.json()["total_questions"] == quiz["total_questions"]

def test_ai_explanation_endpoint(client):
    # Get a question ID from questions list
    q_list = client.get("/api/questions?limit=1").json()
    assert len(q_list) > 0
    test_q_id = q_list[0]["id"]

    res = client.post("/api/ai/explain", json={
        "question_id": test_q_id,
        "user_answer": "Arbitrary Wrong Answer"
    })
    assert res.status_code == 200
    data = res.json()
    assert "why_wrong" in data
    assert "why_correct" in data
    assert "key_takeaway" in data
    assert "full_explanation" in data

def test_ai_tutor_chat_endpoint(client):
    q_list = client.get("/api/questions?limit=1").json()
    test_q_id = q_list[0]["id"] if q_list else None

    res = client.post("/api/ai/tutor", json={
        "question_id": test_q_id,
        "user_message": "Can you explain this question simply?",
        "chat_history": []
    })
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 10
