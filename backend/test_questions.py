import pytest
from unittest.mock import patch, MagicMock
from app.models.medical_report import MedicalReport
from app.questions.services import generate_questions, check_safety
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


def test_check_safety():
    assert check_safety("What does this mean for my daily life?") == True
    assert check_safety("Can you diagnose me based on this?") == False
    assert check_safety("What is the treatment plan?") == False
    assert check_safety("Should I get surgery?") == False
    assert check_safety("What follow-up tests are needed?") == True

@patch('app.questions.services.ChatGoogleGenerativeAI')
@patch('app.questions.services.db.session.commit')
def test_generate_questions(mock_commit, MockLLM, app):
    # Setup mock LLM response
    mock_llm_instance = MagicMock()
    MockLLM.return_value = mock_llm_instance
    
    # We'll mock the chain invoke directly by patching the prompt template chain
    mock_response = MagicMock()
    mock_response.content = '["What does this mean for my daily life?", "What follow-up tests are needed?"]'
    
    with app.app_context():
        # Create a dummy report
        report = MedicalReport(
            user_id="auth0|test",
            file_url="test.pdf",
            upload_date="2024-01-01T00:00:00",
            report_type="Blood Report",
            raw_ocr_output="Test OCR Text",
            explanation_text="Test Explanation"
        )
        
        # We need to save it so it gets an ID and can be queried, or mock the query
        from app.database import db
        db.session.add(report)
        db.session.commit()
        
        with patch('app.questions.services.PromptTemplate') as MockPrompt:
            mock_prompt_instance = MagicMock()
            MockPrompt.from_template.return_value = mock_prompt_instance
            mock_chain = MagicMock()
            mock_prompt_instance.__or__.return_value = mock_chain
            mock_chain.invoke.return_value = mock_response
            
            questions = generate_questions(report.id)
            
            assert isinstance(questions, list)
            assert len(questions) == 2
            assert "What follow-up tests are needed?" in questions
            assert report.generated_questions == questions
