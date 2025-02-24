from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from config import settings
import boto3
import os

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

@app.get("/api/documents")
async def fetch_all_documents():
    try:
        logger.info("Fetching all documents from S3")
        documents = []
        continuation_token = None

        # Loop until all objects have been fetched
        while True:
            if continuation_token:
                response = s3_client.list_objects_v2(
                    Bucket=settings.bucket_name,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3_client.list_objects_v2(
                    Bucket=settings.bucket_name
                )
            
            if 'Contents' in response:
                documents.extend([obj['Key'] for obj in response['Contents']])
            
            if response.get('IsTruncated'):  # There are more objects to fetch
                continuation_token = response.get('NextContinuationToken')
            else:
                break

        logger.info(f"Successfully fetched {len(documents)} documents")
        return JSONResponse(
            status_code=200,
            content={
                "list_of_names": documents
            }
        )
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
