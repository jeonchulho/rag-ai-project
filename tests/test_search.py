"""Tests for search functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestSearchAgent:
    """Test search agent functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_intent_search(self):
        """Test intent detection for search queries."""
        from api.agents.search_agent import SearchAgent, AgentState
        
        # Mock services
        llm_service = Mock()
        vector_store = Mock()
        cache = Mock()
        
        agent = SearchAgent(llm_service, vector_store, cache)
        
        state: AgentState = {
            "query": "search for AI papers",
            "context": {},
            "intent": "",
            "entities": {},
            "search_results": [],
            "summary": "",
            "scheduled_actions": [],
            "response_text": ""
        }
        
        result = await agent._analyze_intent(state)
        assert result["intent"] == "search"
    
    @pytest.mark.asyncio
    async def test_analyze_intent_email(self):
        """Test intent detection for email queries."""
        from api.agents.search_agent import SearchAgent, AgentState
        
        llm_service = Mock()
        vector_store = Mock()
        cache = Mock()
        
        agent = SearchAgent(llm_service, vector_store, cache)
        
        state: AgentState = {
            "query": "email the results to test@example.com",
            "context": {},
            "intent": "",
            "entities": {},
            "search_results": [],
            "summary": "",
            "scheduled_actions": [],
            "response_text": ""
        }
        
        result = await agent._analyze_intent(state)
        assert "email" in result["intent"]
    
    @pytest.mark.asyncio
    async def test_extract_entities(self):
        """Test entity extraction from query."""
        from api.agents.search_agent import SearchAgent, AgentState
        
        llm_service = Mock()
        vector_store = Mock()
        cache = Mock()
        
        agent = SearchAgent(llm_service, vector_store, cache)
        
        state: AgentState = {
            "query": "search AI papers and email to test@example.com at 10 AM",
            "context": {},
            "intent": "",
            "entities": {},
            "search_results": [],
            "summary": "",
            "scheduled_actions": [],
            "response_text": ""
        }
        
        result = await agent._extract_entities(state)
        assert "test@example.com" in result["entities"]["emails"]
        assert len(result["entities"]["times"]) > 0


class TestVectorStore:
    """Test vector store operations."""
    
    def test_connection(self):
        """Test vector store connection."""
        # This would require a running Milvus instance
        # For now, we just test that the class can be imported
        from api.services.vector_store import VectorStoreService
        assert VectorStoreService is not None


class TestLLMService:
    """Test LLM service operations."""
    
    def test_initialization(self):
        """Test LLM service initialization."""
        from api.services.llm_service import LLMService
        
        service = LLMService(
            ollama_endpoints=["http://localhost:11434"],
            model_name="test-model",
            embedding_model="test-embed",
            vision_model="test-vision"
        )
        
        assert service.model_name == "test-model"
        assert len(service.ollama_endpoints) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
