from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from collections import deque

app = FastAPI()

# Data storage in memory (instead of a database)
data_queue = deque(maxlen=100)  # Store the last 100 readings

# Data model
class HealthData(BaseModel):
    bpm: float
    gsr: int

@app.post("/data")
async def receive_data(health_data: HealthData):
    # Add timestamp and store data in memory
    record = {
        "bpm": health_data.bpm,
        "gsr": health_data.gsr,
        "timestamp": datetime.now().isoformat()
    }
    data_queue.append(record)
    return {"status": "success", "received_data": record}

@app.get("/data")
async def get_data():
    # Return the stored data as a list
    return list(data_queue)
