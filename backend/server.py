from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from datetime import date as DateType
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class JournalEntryCreate(BaseModel):
    title: str
    content: str
    tags: List[str] = []

class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    tags: List[str] = []
    mood_score: Optional[int] = None
    mood_emotion: Optional[str] = None
    ai_summary: Optional[str] = None
    date: DateType = Field(default_factory=lambda: datetime.now(timezone.utc).date())
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MoodTrendData(BaseModel):
    date: str
    mood_score: int
    mood_emotion: str

class WeeklyMoodStats(BaseModel):
    weekly_trends: List[MoodTrendData]
    average_mood: float
    most_common_emotion: str
    total_entries: int

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    if isinstance(data.get('date'), DateType):
        data['date'] = data['date'].isoformat()
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    if isinstance(data.get('updated_at'), datetime):
        data['updated_at'] = data['updated_at'].isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item.get('date'), str):
        item['date'] = datetime.fromisoformat(item['date']).date()
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    if isinstance(item.get('updated_at'), str):
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
    return item

# AI Analysis Function
async def analyze_mood_and_summarize(content: str, title: str):
    """Analyze journal entry for mood and generate summary using Gemini LLM"""
    try:
        genai.configure(api_key=os.environ.get('AIzaSyAna4BTNgNm-QrYCZHK-0AVzoUHNOaF4IA'))
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            system_instruction="""You are a mood analysis expert. Analyze the given journal entry and provide:
1. A mood score from 1-10 (where 1 is very negative/sad, 10 is very positive/happy)
2. A primary emotion category (happy, sad, anxious, excited, calm, angry, grateful, stressed, content, melancholy)
3. A brief 2-3 sentence summary of the entry

Respond in this exact JSON format:
{
    "mood_score": 7,
    "mood_emotion": "content",
    "summary": "Brief summary here"
}
"""
        )

        user_message = f"Title: {title}\n\nContent: {content}\n\nPlease analyze this journal entry for mood and provide a summary."

        response = await model.generate_content_async(user_message)

        # Parse the JSON response
        try:
            analysis = json.loads(response.text.strip())
            return {
                "mood_score": analysis.get("mood_score", 5),
                "mood_emotion": analysis.get("mood_emotion", "neutral"),
                "ai_summary": analysis.get("summary", "No summary available")
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "mood_score": 5,
                "mood_emotion": "neutral",
                "ai_summary": "Analysis temporarily unavailable"
            }
            
    except Exception as e:
        logging.error(f"Error in AI analysis: {e}")
        return {
            "mood_score": 5,
            "mood_emotion": "neutral",
            "ai_summary": "Analysis temporarily unavailable"
        }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Journal App API"}

@api_router.post("/entries", response_model=JournalEntry)
async def create_entry(entry_data: JournalEntryCreate):
    """Create a new journal entry with AI mood analysis"""
    try:
        # Get AI analysis
        ai_analysis = await analyze_mood_and_summarize(entry_data.content, entry_data.title)
        
        # Create entry object
        entry = JournalEntry(
            title=entry_data.title,
            content=entry_data.content,
            tags=entry_data.tags,
            mood_score=ai_analysis["mood_score"],
            mood_emotion=ai_analysis["mood_emotion"],
            ai_summary=ai_analysis["ai_summary"]
        )
        
        # Prepare for MongoDB
        entry_dict = prepare_for_mongo(entry.dict())
        
        # Insert into database
        await db.journal_entries.insert_one(entry_dict)
        
        return entry
        
    except Exception as e:
        logging.error(f"Error creating entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to create journal entry")

@api_router.get("/entries", response_model=List[JournalEntry])
async def get_entries(limit: int = 50, skip: int = 0):
    """Get journal entries, sorted by most recent first"""
    try:
        entries = await db.journal_entries.find().sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return [JournalEntry(**parse_from_mongo(entry)) for entry in entries]
    except Exception as e:
        logging.error(f"Error fetching entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch entries")

@api_router.get("/entries/{entry_id}", response_model=JournalEntry)
async def get_entry(entry_id: str):
    """Get a specific journal entry"""
    try:
        entry = await db.journal_entries.find_one({"id": entry_id})
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        return JournalEntry(**parse_from_mongo(entry))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch entry")

@api_router.put("/entries/{entry_id}", response_model=JournalEntry)
async def update_entry(entry_id: str, entry_data: JournalEntryCreate):
    """Update a journal entry and re-analyze mood"""
    try:
        # Get AI analysis for updated content
        ai_analysis = await analyze_mood_and_summarize(entry_data.content, entry_data.title)
        
        # Update data
        update_data = {
            "title": entry_data.title,
            "content": entry_data.content,
            "tags": entry_data.tags,
            "mood_score": ai_analysis["mood_score"],
            "mood_emotion": ai_analysis["mood_emotion"],
            "ai_summary": ai_analysis["ai_summary"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update in database
        result = await db.journal_entries.update_one(
            {"id": entry_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Return updated entry
        updated_entry = await db.journal_entries.find_one({"id": entry_id})
        return JournalEntry(**parse_from_mongo(updated_entry))
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to update entry")

@api_router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str):
    """Delete a journal entry"""
    try:
        result = await db.journal_entries.delete_one({"id": entry_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"message": "Entry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete entry")

@api_router.get("/mood-trends/weekly", response_model=WeeklyMoodStats)
async def get_weekly_mood_trends():
    """Get mood trends for the past 7 days"""
    try:
        # Calculate date 7 days ago
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        
        # Query entries from the last 7 days
        entries = await db.journal_entries.find({
            "date": {"$gte": seven_days_ago.isoformat()},
            "mood_score": {"$ne": None}
        }).sort("date", 1).to_list(length=None)
        
        if not entries:
            return WeeklyMoodStats(
                weekly_trends=[],
                average_mood=5.0,
                most_common_emotion="neutral",
                total_entries=0
            )
        
        # Process trends data
        trends = []
        emotions = []
        total_mood = 0
        
        for entry in entries:
            entry_parsed = parse_from_mongo(entry)
            trends.append(MoodTrendData(
                date=entry_parsed["date"].isoformat(),
                mood_score=entry_parsed["mood_score"],
                mood_emotion=entry_parsed["mood_emotion"]
            ))
            emotions.append(entry_parsed["mood_emotion"])
            total_mood += entry_parsed["mood_score"]
        
        # Calculate stats
        average_mood = total_mood / len(entries) if entries else 5.0
        most_common_emotion = max(set(emotions), key=emotions.count) if emotions else "neutral"
        
        return WeeklyMoodStats(
            weekly_trends=trends,
            average_mood=round(average_mood, 1),
            most_common_emotion=most_common_emotion,
            total_entries=len(entries)
        )
        
    except Exception as e:
        logging.error(f"Error fetching mood trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch mood trends")

@api_router.get("/tags")
async def get_all_tags():
    """Get all unique tags used in entries"""
    try:
        # Use MongoDB aggregation to get unique tags
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$sort": {"_id": 1}}
        ]
        
        results = await db.journal_entries.aggregate(pipeline).to_list(length=None)
        tags = [result["_id"] for result in results if result["_id"]]
        
        return {"tags": tags}
    except Exception as e:
        logging.error(f"Error fetching tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tags")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
