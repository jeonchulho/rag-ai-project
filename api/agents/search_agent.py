"""Search agent using LangGraph for natural language query processing."""

import logging
import re
from typing import Dict, Any, List, TypedDict
from datetime import datetime, timedelta
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the search agent workflow."""
    query: str
    context: Dict[str, Any]
    intent: str
    entities: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    summary: str
    scheduled_actions: List[Dict[str, Any]]
    response_text: str


class SearchAgent:
    """
    Agent for processing natural language queries using LangGraph workflow.
    
    Handles complex queries like:
    "Search AI papers, summarize them, and email the summary to hong@example.com at 10 AM"
    """
    
    def __init__(self, llm_service, vector_store, cache):
        """
        Initialize search agent.
        
        Args:
            llm_service: LLM service for text generation
            vector_store: Vector store for similarity search
            cache: Cache service
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.cache = cache
        logger.info("Search agent initialized")
    
    async def process_natural_language(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process natural language query through agent workflow.
        
        Args:
            query: Natural language query
            context: Additional context
            
        Returns:
            Processing results with intent, entities, results, and actions
        """
        # Initialize state
        state: AgentState = {
            "query": query,
            "context": context,
            "intent": "",
            "entities": {},
            "search_results": [],
            "summary": "",
            "scheduled_actions": [],
            "response_text": ""
        }
        
        # Execute workflow
        state = await self._analyze_intent(state)
        state = await self._extract_entities(state)
        state = await self._execute_search(state)
        state = await self._summarize_results(state)
        state = await self._schedule_actions(state)
        state = await self._finalize(state)
        
        return {
            "intent": state["intent"],
            "entities": state["entities"],
            "search_results": [
                {
                    "id": r.get("id", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "metadata": r.get("metadata", {}),
                    "document_type": r.get("document_type", "")
                }
                for r in state["search_results"]
            ],
            "summary": state["summary"],
            "scheduled_actions": state["scheduled_actions"],
            "response_text": state["response_text"]
        }
    
    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """Analyze user intent from query."""
        query = state["query"].lower()
        
        # Simple intent detection
        if "search" in query or "find" in query:
            state["intent"] = "search"
        elif "summarize" in query or "summary" in query:
            state["intent"] = "search_and_summarize"
        elif "email" in query or "send" in query:
            state["intent"] = "search_summarize_email"
        else:
            state["intent"] = "search"
        
        logger.info(f"Detected intent: {state['intent']}")
        return state
    
    async def _extract_entities(self, state: AgentState) -> AgentState:
        """Extract entities from query."""
        query = state["query"]
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query)
        
        # Extract time expressions
        time_patterns = [
            r'at (\d{1,2})\s*(AM|PM|am|pm)',
            r'at (\d{1,2}:\d{2})\s*(AM|PM|am|pm)?',
            r'tomorrow',
            r'next (week|month|day)'
        ]
        
        times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, query)
            if matches:
                times.extend(matches)
        
        # Extract search keywords (remove common words)
        keywords = query
        for stop_word in ["search", "find", "summarize", "email", "send", "at", "to", "the", "and"]:
            keywords = re.sub(rf'\b{stop_word}\b', '', keywords, flags=re.IGNORECASE)
        keywords = " ".join(keywords.split())
        
        state["entities"] = {
            "emails": emails,
            "times": times,
            "keywords": keywords
        }
        
        logger.info(f"Extracted entities: {state['entities']}")
        return state
    
    async def _execute_search(self, state: AgentState) -> AgentState:
        """Execute search based on extracted keywords."""
        if state["intent"] in ["search", "search_and_summarize", "search_summarize_email"]:
            keywords = state["entities"].get("keywords", state["query"])
            
            try:
                # Generate query embedding
                query_embedding = await self.llm_service.embed_text(keywords)
                
                # Search all collections
                results = self.vector_store.search_all(query_embedding, top_k=5)
                state["search_results"] = results
                
                logger.info(f"Found {len(results)} search results")
            except Exception as e:
                logger.error(f"Search execution failed: {e}")
                state["search_results"] = []
        
        return state
    
    async def _summarize_results(self, state: AgentState) -> AgentState:
        """Summarize search results if requested."""
        if state["intent"] in ["search_and_summarize", "search_summarize_email"]:
            if state["search_results"]:
                # Combine result contents
                combined_text = "\n\n".join([
                    r.get("content", "") for r in state["search_results"]
                ])
                
                try:
                    summary = await self.llm_service.summarize(combined_text)
                    state["summary"] = summary
                    logger.info("Generated summary")
                except Exception as e:
                    logger.error(f"Summarization failed: {e}")
                    state["summary"] = "Summary generation failed"
        
        return state
    
    async def _schedule_actions(self, state: AgentState) -> AgentState:
        """Schedule actions like email sending."""
        if state["intent"] == "search_summarize_email":
            emails = state["entities"].get("emails", [])
            times = state["entities"].get("times", [])
            
            for email in emails:
                scheduled_time = None
                
                # Parse time if provided
                if times:
                    scheduled_time = self._parse_time(times[0])
                
                action = {
                    "action_type": "email",
                    "parameters": {
                        "to": email,
                        "subject": "Search Results Summary",
                        "body": state["summary"] or "No summary available"
                    },
                    "scheduled_time": scheduled_time.isoformat() if scheduled_time else None
                }
                
                state["scheduled_actions"].append(action)
                logger.info(f"Scheduled email to {email}")
        
        return state
    
    def _parse_time(self, time_str: Any) -> datetime:
        """Parse time string to datetime."""
        try:
            if isinstance(time_str, tuple):
                time_str = " ".join(str(t) for t in time_str)
            
            # Try parsing with dateutil
            return date_parser.parse(time_str)
        except Exception as e:
            logger.warning(f"Time parsing failed: {e}, using 1 hour from now")
            return datetime.now() + timedelta(hours=1)
    
    async def _finalize(self, state: AgentState) -> AgentState:
        """Generate final response text."""
        parts = []
        
        if state["search_results"]:
            parts.append(f"Found {len(state['search_results'])} relevant results.")
        
        if state["summary"]:
            parts.append("Generated summary of the results.")
        
        if state["scheduled_actions"]:
            parts.append(f"Scheduled {len(state['scheduled_actions'])} action(s).")
        
        state["response_text"] = " ".join(parts) if parts else "Query processed successfully."
        
        return state
