# backend/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import List
from pydantic import BaseModel
from backend.src.news_utils import db_connection
from backend.src.models import MediaSource
from datetime import datetime
from backend.src.log_utils import api_logger, health_logger
import os
import psutil
import time
import dateutil.tz
import sqlite3
import logging
from fastapi import Query
from pydantic import HttpUrl, Field, field_validator
import re
from backend.src.media_utils import get_all_media_sources

app = FastAPI(
    title="Concordia API",
    description="Harmony in the Noise: API for analyzing media bias and narratives",
    version="1.0.0",
)

# Enable CORS to allow the frontend to access the API
origins = [
    "http://localhost:8080", # React Dev Server
    "http://127.0.0.1:8080", # Alternative for localhost
    # Add any other origins if needed, e.g., your production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins allowed
    allow_credentials=True, # Allow cookies to be included in requests
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers
)


# Pydantic models for API responses
class Article(BaseModel):
    id: str
    source_name: str
    raw_title: str
    raw_description: str
    clean_content: str
    categories: str
    link: str
    publication_date: str
    created_at: str


class Analysis(BaseModel):
    id: str
    source_name: str
    analysis_date: str
    numbers_of_articles: int
    main_narrative_theme_1: str | None
    main_narrative_coverage_1: float
    main_narrative_examples_1: str | None
    main_narrative_theme_2: str | None
    main_narrative_coverage_2: float
    main_narrative_examples_2: str | None
    main_narrative_theme_3: str | None
    main_narrative_coverage_3: float
    main_narrative_examples_3: str | None
    main_narrative_theme_4: str | None
    main_narrative_coverage_4: float
    main_narrative_examples_4: str | None
    main_narrative_theme_5: str | None
    main_narrative_coverage_5: float
    main_narrative_examples_5: str | None
    main_narrative_confidence: float
    sentiment_positive_percentage: float
    sentiment_negative_percentage: float
    sentiment_neutral_percentage: float
    sentiment_confidence: float
    bias_political_score: float
    bias_political_leaning: str | None
    bias_supporting_evidence: str | None
    bias_confidence: float
    values_promoted_value_1: str | None
    values_promoted_examples_1: str | None
    values_promoted_value_2: str | None
    values_promoted_examples_2: str | None
    values_promoted_value_3: str | None
    values_promoted_examples_3: str | None
    values_promoted_confidence: float
    created_at: str


# Root endpoint to redirect to API docs
@app.get("/")
async def root():
    """
    Redirects the root URL to the API documentation.
    """
    return RedirectResponse(url="/docs")


# API Endpoints
@app.get("/articles", response_model=List[Article])
async def get_articles(source: str | None = None, date: str | None = None, keyword: str | None = None):
    """
    Retrieve articles from the database, optionally filtered by source, date, and keyword.

    Args:
        source (str, optional): Filter by source name (e.g., 'fox_news').
        date (str, optional): Filter by publication date (YYYY-MM-DD).
        keyword (str, optional): Filter by keyword in article title or content.

    Returns:
        List[Article]: A list of articles.
    """
    query = """
        SELECT a.id, s.name AS source_name, a.raw_title, a.raw_description, 
               a.clean_content, a.categories, a.link, a.publication_date, a.created_at
        FROM articles a
        JOIN sources s ON a.source_id = s.source_id
        WHERE 1=1
    """
    params = []
    if source:
        query += " AND s.name = ?"
        params.append(source)
    if date:
        query += " AND strftime('%Y-%m-%d', a.publication_date) = ?"
        params.append(date)
    if keyword:
        query += " AND (a.raw_title LIKE ? OR a.clean_content LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        articles = []
        for row in rows:
            article = {
                "id": row[0],
                "source_name": row[1],
                "raw_title": row[2],
                "raw_description": row[3],
                "clean_content": row[4],
                "categories": row[5],
                "link": row[6],
                "publication_date": row[7],
                "created_at": row[8]
            }
            articles.append(article)
        
        return articles


@app.get("/analyses", response_model=List[Analysis])
async def get_analyses(source: str | None = None, date: str | None = None):
    """
    Retrieve analysis results from the database, optionally filtered by source and date.

    Args:
        source (str, optional): Filter by source name (e.g., 'fox_news').
        date (str, optional): Filter by analysis date in ISO format (e.g., '2025-03-03').

    Returns:
        List[Analysis]: A list of analysis results.
    """
    query = """
        SELECT a.id, s.name AS source_name, a.analysis_date, a.numbers_of_articles,
               a.main_narrative_theme_1, a.main_narrative_coverage_1, a.main_narrative_examples_1,
               a.main_narrative_theme_2, a.main_narrative_coverage_2, a.main_narrative_examples_2,
               a.main_narrative_theme_3, a.main_narrative_coverage_3, a.main_narrative_examples_3,
               a.main_narrative_theme_4, a.main_narrative_coverage_4, a.main_narrative_examples_4,
               a.main_narrative_theme_5, a.main_narrative_coverage_5, a.main_narrative_examples_5,
               a.main_narrative_confidence,
               a.sentiment_positive_percentage, a.sentiment_negative_percentage, a.sentiment_neutral_percentage,
               a.sentiment_confidence,
               a.bias_political_score, a.bias_political_leaning, a.bias_supporting_evidence, a.bias_confidence,
               a.values_promoted_value_1, a.values_promoted_examples_1,
               a.values_promoted_value_2, a.values_promoted_examples_2,
               a.values_promoted_value_3, a.values_promoted_examples_3,
               a.values_promoted_confidence, a.created_at
        FROM analyses a
        JOIN sources s ON a.source_id = s.source_id
        WHERE 1=1
    """
    params = []
    if source:
        query += " AND s.name = ?"
        params.append(source)
    if date:
        # Ensure the date is in the correct format
        try:
            # This assumes the input date is in the format 'YYYY-MM-DD'
            datetime.strptime(date, "%Y-%m-%d")
            query += " AND a.analysis_date = ?"
            params.append(date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Please use YYYY-MM-DD."
            )

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        analyses = [
            Analysis(
                id=row["id"],
                source_name=row["source_name"],
                analysis_date=row["analysis_date"],
                numbers_of_articles=row["numbers_of_articles"],
                main_narrative_theme_1=row["main_narrative_theme_1"],
                main_narrative_coverage_1=row["main_narrative_coverage_1"],
                main_narrative_examples_1=row["main_narrative_examples_1"],
                main_narrative_theme_2=row["main_narrative_theme_2"],
                main_narrative_coverage_2=row["main_narrative_coverage_2"],
                main_narrative_examples_2=row["main_narrative_examples_2"],
                main_narrative_theme_3=row["main_narrative_theme_3"],
                main_narrative_coverage_3=row["main_narrative_coverage_3"],
                main_narrative_examples_3=row["main_narrative_examples_3"],
                main_narrative_theme_4=row["main_narrative_theme_4"],
                main_narrative_coverage_4=row["main_narrative_coverage_4"],
                main_narrative_examples_4=row["main_narrative_examples_4"],
                main_narrative_theme_5=row["main_narrative_theme_5"],
                main_narrative_coverage_5=row["main_narrative_coverage_5"],
                main_narrative_examples_5=row["main_narrative_examples_5"],
                main_narrative_confidence=row["main_narrative_confidence"],
                sentiment_positive_percentage=row["sentiment_positive_percentage"],
                sentiment_negative_percentage=row["sentiment_negative_percentage"],
                sentiment_neutral_percentage=row["sentiment_neutral_percentage"],
                sentiment_confidence=row["sentiment_confidence"],
                bias_political_score=row["bias_political_score"],
                bias_political_leaning=row["bias_political_leaning"],
                bias_supporting_evidence=row["bias_supporting_evidence"],
                bias_confidence=row["bias_confidence"],
                values_promoted_value_1=row["values_promoted_value_1"],
                values_promoted_examples_1=row["values_promoted_examples_1"],
                values_promoted_value_2=row["values_promoted_value_2"],
                values_promoted_examples_2=row["values_promoted_examples_2"],
                values_promoted_value_3=row["values_promoted_value_3"],
                values_promoted_examples_3=row["values_promoted_examples_3"],
                values_promoted_confidence=row["values_promoted_confidence"],
                created_at=row["created_at"],
            )
            for row in cursor.fetchall()
        ]
    return analyses


@app.get("/media_sources", response_model=List[MediaSource])
async def get_media_sources():
    """
    Retrieve all media sources with their metadata and bias ratings.

    Fetches all records from the media_sources table and returns them
    as a list of MediaSource objects. Handles potential database errors.
    """
    # Log the request entry
    api_logger.info("Request received for /media_sources")
    try:
        # Use the utility function to get all sources
        media_sources = get_all_media_sources()
        # Log successful retrieval
        api_logger.info(f"Successfully retrieved {len(media_sources)} media sources.")
        # Return the list of media sources
        return media_sources
    except sqlite3.Error as e:
        # Log the database error
        api_logger.error(f"Database error in /media_sources: {e}", exc_info=True)
        # Raise an HTTP exception for internal server error
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        # Log any other unexpected errors
        api_logger.error(f"Unexpected error in /media_sources: {e}", exc_info=True)
        # Raise an HTTP exception for internal server error
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint that returns the status of all components.
    """
    health_logger.info("Health check requested")
    
    # Check database connection
    db_status = "healthy"
    db_message = "Database connection successful"
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database connection failed: {str(e)}"
        health_logger.error(db_message)
    
    # Check log files
    log_files = {
        "collector": os.path.exists("logs/collector.log"),
        "analyzer": os.path.exists("logs/analyzer.log"),
        "api": os.path.exists("logs/api.log"),
        "maintenance": os.path.exists("logs/maintenance.log"),
        "health": os.path.exists("logs/health.log"),
        "resources": os.path.exists("logs/resources.log")
    }
    
    # Check system resources
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    resources = {
        "cpu_percent": process.cpu_percent(interval=0.1),
        "memory_usage_mb": memory_info.rss / (1024 * 1024),
        "uptime_seconds": time.time() - process.create_time()
    }
    
    # Check last collection and analysis times
    last_collection = "unknown"
    last_analysis = "unknown"
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(created_at) FROM articles")
            result = cursor.fetchone()
            if result and result[0]:
                last_collection = result[0]
                
            cursor.execute("SELECT MAX(created_at) FROM analyses")
            result = cursor.fetchone()
            if result and result[0]:
                last_analysis = result[0]
    except Exception as e:
        health_logger.error(f"Error checking last activity times: {str(e)}")
    
    health_status = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": {
            "status": db_status,
            "message": db_message
        },
        "logs": log_files,
        "resources": resources,
        "last_activity": {
            "collection": last_collection,
            "analysis": last_analysis
        },
        "timestamp": datetime.now(dateutil.tz.UTC).isoformat()
    }
    
    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
