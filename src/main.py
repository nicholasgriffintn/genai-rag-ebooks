from fastapi import FastAPI, Request
import logging
import requests
import json

from utils import extract_main_content, split_into_paragraphs, clean_text, read_file

async def on_fetch(request, env):
    import asgi

    return await asgi.fetch(app, request, env)


app = FastAPI()

"""
This is the homepage route, it will display the frontend.
"""
@app.get("/")
async def homepage():
    return {"message": "Hello, World!"}

"""
This is the request to begin the ingestion process.

The process will:
- Fetch the book from the cache.
- Extract the main content.
- Clean the text.
- Query the model.
- Save the vectors.

TODO: Change this to a post

Args:
    req (Request): The request object.
"""
@app.get("/ingest")
async def ingest(req: Request):
    try:
        env = req.scope['env']
        
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        """
        TODO:
        
        - Will need to vectorize the text within the book into CloudFlare Vectorize.
        - Use a RAG model to generate responses to questions about the book.
        - Will need to build a simple API to interact with the chatbot.
        - Will need to build a simple frontend to interact with the chatbot.
        """
        
        if not env.BOOKS:
            logger.info('Books cache not found!')
            return {
                "message": "Books cache not found!",
                "status": 404
            }
        
        book_key = 'alice-in-wonderland'
        logger.info(f'Fetching book with key: {book_key}')
        book_text = await env.BOOKS.get(book_key)
        
        if not book_text:
            logger.info('Book not found!')
            return {
                "message": "Book not found!",
                "status": 404
            }
        
        logger.info('Extracting main content...')
        main_content = extract_main_content(book_text)
        paragraphs = split_into_paragraphs(main_content)
        cleaned_paragraphs = clean_text(paragraphs)
        joined_paragraphs = ' '.join(cleaned_paragraphs)
        
        logger.info("Querying model...")
        """
        TODO: This doesn't work, I don't know why.
        ERROR:main:AiError: 5006: must have required property 'text'
        """
        """
        model = await env.AI.run(
            "@cf/baai/bge-large-en-v1.5",
            { "text": [joined_paragraphs] },
            {
                gateway: {
                    id: "genai-rag-ebooks",
                    skipCache: false,
                    cacheTtl: 3360,
                },
            },
        )
        """
        API_BASE_URL = f"https://gateway.ai.cloudflare.com/v1/{env.ACCOUNT_ID}/genai-rag-ebooks/workers-ai/@cf/baai/bge-large-en-v1.5"
        logger.info(f'API_BASE_URL: {API_BASE_URL}')
        model_headers = {
            "Authorization": f"Bearer {env.API_TOKEN}",
            "Content-Type": "application/json"
        }
        model_input = { "text": [joined_paragraphs] }
        model_response = requests.post(API_BASE_URL, headers=model_headers, json=model_input)
        model = model_response.json()
        
        if not model or not model['data']:
            logger.info('Model returned no data!')
            return {
                "message": "Model returned no data!",
                "status": 500
            }
        
        vectors = []
        id = 1
        for vector in model['data']:
            vectors.append({
                "book": book_key,
                "id": id,
                "vector": vector
            })
            id += 1
            
        logger.info('Saving vectors...')
        inserted = await env.VECTORIZE.upsert(vectors)
        logger.info(f'Inserted: {inserted}')

        logger.info('Done!')
        return {
            "message": "Done!",
            "status": 200
        }
    except Exception as e:
        logger.error(e)
        return {
            "message": "Internal Server Error!",
            "status": 500
        }
