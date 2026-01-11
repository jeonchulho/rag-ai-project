from api.utils.text_processing import clean_text, extract_keywords

class SearchAgent:
    def _analyze_intent(self, text, state):
        """
        Analyzes the user intent from the text and updates the agent state.
        """
        cleaned_text = clean_text(text)
        keywords = extract_keywords(cleaned_text)
        # Use keywords to decide intent (for demo purposes)
        if 'find' in keywords or 'search' in keywords:
            state['intent'] = 'search'
        elif 'define' in keywords:
            state['intent'] = 'define'
        else:
            state['intent'] = 'unknown'
        state['entities'] = keywords
        return state

    def _extract_entities(self, text, state):
        """
        Extracts entities from text using extract_keywords and updates state entities.
        """
        cleaned_text = clean_text(text)
        keywords = extract_keywords(cleaned_text)
        state['entities'] = keywords
        return state

    # ... rest of the class remains unchanged ...

# ... rest of the module ...
