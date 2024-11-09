from js import Response
import logging
import re

def extract_main_content(text):
    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK ALICE'S ADVENTURES IN WONDERLAND ***"
    end_marker = "THE END"
    
    start_index = text.find(start_marker) + len(start_marker)
    end_index = text.find(end_marker)
    
    return text[start_index:end_index]

def split_into_paragraphs(text):
    return text.split('\n\n')

def clean_text(paragraphs):
    cleaned_paragraphs = []
    for paragraph in paragraphs:
        # Remove unwanted patterns
        paragraph = re.sub(r'\[.*?\]', '', paragraph)
        paragraph = re.sub(r'\*{2,}', '', paragraph)
        paragraph = re.sub(r'^\s*$', '', paragraph)
        cleaned_paragraphs.append(paragraph.strip())
        
        """
        TODO: Need to remove other initial content like:
        Alice’s Adventures in Wonderland

        by Lewis Carroll

        THE MILLENNIUM FULCRUM EDITION 3.0

        Contents

        CHAPTER I.     Down the Rabbit-Hole
        *      *      *      *      *      *      *

        *      *      *      *      *      *      *
        """
    return [p for p in cleaned_paragraphs if p]

async def on_fetch(request, env):
    try:
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        
        """
        TODO:
        
        - Will need to vectorize the text within the book into CloudFlare Vectorize.
        - Use a RAG model to generate responses to questions about the book.
        - Will need to build a simple API to interact with the chatbot.
        - Will need to build a simple frontend to interact with the chatbot.
        """
        
        book_key = 'alice-in-wonderland'
        logger.debug(f'Fetching book with key: {book_key}')
        book_text = await env.BOOKS.get(book_key);
        
        if not book_text:
            logger.debug('Book not found!')
            return Response.new("Book not found!", status=404)
        
        logger.debug('Extracting main content...')
        main_content = extract_main_content(book_text)
        paragraphs = split_into_paragraphs(main_content)
        cleaned_paragraphs = clean_text(paragraphs)
        joined_paragraphs = ' '.join(cleaned_paragraphs)
        
        logger.debug("Querying model...")
        model_prompt = {'text': [joined_paragraphs]}
        model = await env.AI.run(
            "@cf/baai/bge-base-en-v1.5",
            model_prompt
        )
        
        vectors = []
        id = 1
        for vector in model['data']:
            vectors.append({
                "book": book_key,
                "id": id,
                "vector": vector
            })
            id += 1
            
        logger.debug('Saving vectors...')
        inserted = await env.VECTORIZE.upsert(vectors)
        logger.debug(f'Inserted: {inserted}')

        logger.debug('Done!')
        return Response.new(inserted, status=200)
    except Exception as e:
        logger.error(e)
        return Response.new("An error occurred!", status=500)
