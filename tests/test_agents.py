"""Tests for agent workflows."""

import pytest
from unittest.mock import Mock, AsyncMock


class TestSearchAgentWorkflow:
    """Test the complete search agent workflow."""
    
    @pytest.mark.asyncio
    async def test_simple_search_workflow(self):
        """Test simple search workflow."""
        from api.agents.search_agent import SearchAgent
        
        # Mock services
        llm_service = Mock()
        llm_service.embed_text = AsyncMock(return_value=[0.1] * 768)
        llm_service.summarize = AsyncMock(return_value="Test summary")
        
        vector_store = Mock()
        vector_store.search_all = Mock(return_value=[
            {
                "id": "doc1",
                "content": "Test content",
                "score": 0.95,
                "metadata": {},
                "document_type": "text"
            }
        ])
        
        cache = Mock()
        
        agent = SearchAgent(llm_service, vector_store, cache)
        
        result = await agent.process_natural_language(
            query="search for AI papers",
            context={}
        )
        
        assert "intent" in result
        assert "entities" in result
        assert "response_text" in result
    
    @pytest.mark.asyncio
    async def test_email_workflow(self):
        """Test workflow with email scheduling."""
        from api.agents.search_agent import SearchAgent
        
        llm_service = Mock()
        llm_service.embed_text = AsyncMock(return_value=[0.1] * 768)
        llm_service.summarize = AsyncMock(return_value="Test summary")
        
        vector_store = Mock()
        vector_store.search_all = Mock(return_value=[])
        
        cache = Mock()
        
        agent = SearchAgent(llm_service, vector_store, cache)
        
        result = await agent.process_natural_language(
            query="search papers and email to test@example.com",
            context={}
        )
        
        # Intent detection is flexible - check that email is involved
        assert "email" in result["intent"] or len(result["scheduled_actions"]) > 0 or "test@example.com" in str(result["entities"])


class TestActionAgent:
    """Test action agent."""
    
    @pytest.mark.asyncio
    async def test_execute_email_action(self):
        """Test email action execution."""
        from api.agents.action_agent import ActionAgent
        
        agent = ActionAgent()
        
        result = await agent.execute_action(
            action_type="email",
            parameters={
                "to": "test@example.com",
                "subject": "Test",
                "body": "Test body"
            }
        )
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        """Test unknown action type."""
        from api.agents.action_agent import ActionAgent
        
        agent = ActionAgent()
        
        result = await agent.execute_action(
            action_type="unknown",
            parameters={}
        )
        
        assert result["status"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
