import os
import pytest
import requests

API_BASE = "http://localhost:8000/api/v1"
PDF_PATH = "tests/test_resources/aaa.PDF"
TEST_EMAIL = "jeonchulho@email.com"

@pytest.fixture(scope="session", autouse=True)
def ensure_pdf():
    # 테스트 PDF 없으면 생성
    if not os.path.isfile(PDF_PATH):
        import sys
        sys.path.insert(0, "tests")
        from create_test_pdf import create_test_pdf
        create_test_pdf(PDF_PATH)

@pytest.fixture(scope="session")
def upload_document():
    """aaa.PDF를 업로드하고 document_id를 반환"""
    with open(PDF_PATH, "rb") as f:
        files = {"file": f}
        resp = requests.post(f"{API_BASE}/upload/document", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "document_id" in data
    return data["document_id"]

def test_pdf_summarize_and_email(upload_document):
    """PDF 요약 후 이메일 예약까지 검증"""
    query = (
        f"aaa.PDF 내용을 요약해서 전철호({TEST_EMAIL})에게 10시에 메일을 보내줘"
    )
    resp = requests.post(
        f"{API_BASE}/search",
        json={
            "query": query,
            "search_type": "document"
        }
    )
    assert resp.status_code == 200
    result = resp.json()

    assert result["intent"] in [
        "search_summarize_email", "search_and_summarize", "search"
    ]
    assert TEST_EMAIL in result["entities"].get("emails", [])
    assert any("10" in str(t) for t in result["entities"].get("times", []))
    assert isinstance(result.get("summary"), str) and len(result["summary"]) > 0

    scheduled = result.get("scheduled_actions", [])
    assert scheduled
    action = scheduled[0]
    assert action["action_type"] == "email"
    assert action["parameters"]["to"] == TEST_EMAIL
    assert action["scheduled_time"] is not None
    assert "메일" in result.get("response_text", "") or "Summary" in result.get("response_text", "")
