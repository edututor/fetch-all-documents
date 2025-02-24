from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
import boto3
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    aws_access_key: str
    aws_secret_key: str
    bucket_name: str

    def __init__(self, **data):
        super().__init__(**data)

settings = Settings()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key,
    aws_secret_access_key=settings.aws_secret_key
)

def calculate_total_pages(total_items: int, page_size: int) -> int:
    return -(-total_items // page_size)  # Ceiling division

def get_start_key(page: int, page_size: int) -> int:
    return (page - 1) * page_size

@app.get("/api/documents")
async def fetch_all_documents(page: int = 1, page_size: int = 20):
    try:
        logger.info("Fetching documents from S3")

        response = s3_client.list_objects_v2(
            Bucket=settings.bucket_name,
            MaxKeys=page_size,
            StartAfter='' if page == 1 else get_start_key(page, page_size)
        )

        documents = []
        if 'Contents' in response:
            documents = [obj['Key'] for obj in response['Contents']]
        logger.info(f"Successfully fetched {len(documents)} documents")
        
        return JSONResponse(
            status_code=200,
            content={
                "list_of_names": documents,
                "has_more": response.get('IsTruncated', False),
                "total_pages": calculate_total_pages(response.get('KeyCount', 0), page_size),
                "current_page": page
            }
        )
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)