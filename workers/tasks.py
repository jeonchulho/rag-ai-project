from api.utils.text_processing import extract_text_from_file, smart_chunk, clean_text, extract_keywords

# ... other imports and code ...

def process_document_task(file_path):
    # Extract raw text from the file
    raw_text = extract_text_from_file(file_path)
    # Clean the text if needed
    cleaned_text = clean_text(raw_text)
    # Chunk the text using smart_chunk
    chunks = smart_chunk(cleaned_text)

    chunk_results = []
    for chunk in chunks:
        keywords = extract_keywords(chunk)
        chunk_results.append({
            "chunk": chunk,
            "keywords": keywords
        })

    # Return a structure including each chunk and its keywords
    return {
        "chunks": chunk_results,
        "file_path": file_path
    }

# ... rest of the code ...
