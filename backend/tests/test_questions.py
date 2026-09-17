import uuid
import pytest

def test_health_endpoints(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_pg = client.get("/health/postgres")
    assert res_pg.status_code == 200
    assert res_pg.json()["status"] == "CONNECTED"

def test_create_mcq_success(client):
    payload = {
        "question_type": "MCQ",
        "question_text": "What is the capital of Rajasthan?",
        "options": ["A. Jaipur", "B. Jodhpur", "C. Udaipur", "D. Kota"],
        "correct_answer": "A. Jaipur",
        "explanation": "Jaipur is famously known as the Pink City and is the capital of Rajasthan.",
        "subject": "Rajasthan GK",
        "chapter": "Geography",
        "topic": "Capitals & Major Cities",
        "difficulty": "EASY",
        "tags": ["Rajasthan", "Capital", "GK"],
        "is_pyq": True,
        "exam_name": "REET",
        "exam_year": 2024,
        "exam_month": 5,
        "exam_day": 12,
        "source": "REET Official Paper 2024"
    }
    response = client.post("/api/questions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["question_type"] == "MCQ"
    assert data["question_text"] == payload["question_text"]
    assert data["options"] == payload["options"]
    assert data["correct_answer"] == payload["correct_answer"]
    assert "id" in data

    # Cleanup
    q_id = data["id"]
    client.delete(f"/api/questions/{q_id}")

def test_create_mcq_missing_options_fails(client):
    payload = {
        "question_type": "MCQ",
        "question_text": "What is the capital of Rajasthan?",
        "correct_answer": "Jaipur",
        "subject": "Rajasthan GK",
        "chapter": "Geography",
        "topic": "Capitals",
        "difficulty": "EASY"
    }
    response = client.post("/api/questions", json=payload)
    assert response.status_code == 422

def test_create_single_answer_success(client):
    payload = {
        "question_type": "SINGLE_ANSWER",
        "question_text": "Who founded the city of Jaipur in 1727?",
        "correct_answer": "Maharaja Sawai Jai Singh II",
        "explanation": "Sawai Jai Singh II founded the city of Jaipur in November 1727.",
        "subject": "Rajasthan GK",
        "chapter": "Rajasthan History",
        "topic": "Kachwaha Dynasty",
        "difficulty": "MEDIUM",
        "tags": ["History", "Jaipur", "Founders"],
        "is_pyq": True,
        "exam_name": "RPSC RAS",
        "exam_year": 2021,
        "source": "RAS Prelims 2021"
    }
    response = client.post("/api/questions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["question_type"] == "SINGLE_ANSWER"
    assert data["correct_answer"] == payload["correct_answer"]
    assert data["options"] is None

    # Cleanup
    client.delete(f"/api/questions/{data['id']}")

def test_create_note_success(client):
    payload = {
        "question_type": "NOTE",
        "question_text": "The Prajamandal movements in Rajasthan were people's movements for constitutional reforms and responsible governance under the aegis of the princely states.",
        "subject": "Rajasthan GK",
        "chapter": "Rajasthan History",
        "topic": "Prajamandal Movement",
        "difficulty": "MEDIUM",
        "tags": ["Notes", "Freedom Movement", "Prajamandal"],
        "is_pyq": False
    }
    response = client.post("/api/questions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["question_type"] == "NOTE"
    assert data["correct_answer"] is None
    assert data["options"] is None

    # Cleanup
    client.delete(f"/api/questions/{data['id']}")

def test_crud_lifecycle(client):
    # 1. Create
    payload = {
        "question_type": "MCQ",
        "question_text": "Which lake in Rajasthan is famous for salt production?",
        "options": ["A. Sambhar Lake", "B. Pichola Lake", "C. Fateh Sagar", "D. Ana Sagar"],
        "correct_answer": "A. Sambhar Lake",
        "subject": "Rajasthan GK",
        "chapter": "Geography",
        "topic": "Lakes of Rajasthan",
        "difficulty": "EASY",
        "tags": ["Geography", "Lakes"],
        "is_pyq": True,
        "exam_name": "CET",
        "exam_year": 2023
    }
    res = client.post("/api/questions", json=payload)
    assert res.status_code == 201
    q_id = res.json()["id"]

    # 2. Read by ID
    res_get = client.get(f"/api/questions/{q_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == q_id

    # 3. List with filter
    res_list = client.get(f"/api/questions?subject=Rajasthan GK&is_pyq=true&exam_name=CET")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(item["id"] == q_id for item in items)

    # 4. Update
    update_payload = {
        "difficulty": "MEDIUM",
        "explanation": "Sambhar Salt Lake is India's largest inland salt lake."
    }
    res_put = client.put(f"/api/questions/{q_id}", json=update_payload)
    assert res_put.status_code == 200
    assert res_put.json()["difficulty"] == "MEDIUM"
    assert res_put.json()["explanation"] == update_payload["explanation"]

    # 5. Delete
    res_del = client.delete(f"/api/questions/{q_id}")
    assert res_del.status_code == 200

    # 6. Verify 404
    res_not_found = client.get(f"/api/questions/{q_id}")
    assert res_not_found.status_code == 404
