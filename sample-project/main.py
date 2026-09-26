"""
Todo API — main application.

NOTE: This file is intentionally flawed for DevFlow AI analysis.
See sample-project/README.md for the full list of seeded issues.
"""
import datetime  # SP-13: unused import

from bson import ObjectId
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI(title="Todo API")

# SP-01: Hardcoded MongoDB connection string with credentials
client = MongoClient("mongodb://admin:secret123@localhost:27017/tododb")
db = client["tododb"]


@app.get("/todos")
def get_todos():
    # SP-07: No pagination — returns ALL documents
    # SP-08: Duplicate db connection logic (client used directly, not via dependency)
    # SP-09: Magic string "todos" repeated
    # SP-12: No docstring
    todos = list(db["todos"].find())  # SP-09
    for todo in todos:
        todo["_id"] = str(todo["_id"])
    return todos


@app.post("/todos")
def create_todo(todo: dict):
    # SP-02: No input validation — empty string and XSS content accepted
    # SP-08: Duplicate db reference
    # SP-09: Magic string "todos" repeated
    # SP-12: No docstring
    result = db["todos"].insert_one(todo)  # SP-09
    return {"id": str(result.inserted_id)}


@app.get("/todos/{todo_id}")
def get_todo(todo_id: str):
    # SP-05: ObjectId not validated — invalid ID causes unhandled exception (500)
    # SP-12: No docstring
    todo = db["todos"].find_one({"_id": ObjectId(todo_id)})  # SP-09
    if todo is None:
        return {"error": "not found"}
    todo["_id"] = str(todo["_id"])
    return todo


@app.put("/todos/{todo_id}")
def update_todo(todo_id: str, update: dict):
    # SP-03: Silent success when ID does not exist — matched_count not checked
    # SP-05: ObjectId not validated
    # SP-12: No docstring
    db["todos"].update_one(  # SP-09
        {"_id": ObjectId(todo_id)},
        {"$set": update},
    )
    return {"status": "updated"}


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    # SP-04: Silent success when ID does not exist — deleted_count not checked
    # SP-05: ObjectId not validated
    # SP-12: No docstring
    db["todos"].delete_one({"_id": ObjectId(todo_id)})  # SP-09
    return {"status": "deleted"}
