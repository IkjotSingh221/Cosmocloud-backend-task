from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import pymongo
from bson import ObjectId
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_STRING")
if not MONGO_DETAILS:
    raise ValueError("MONGO_STRING environment variable is not set!")

# Initialize MongoDB client
client = pymongo.MongoClient(MONGO_DETAILS)
database = client["student_management"]
student_collection = database["students"]

# FastAPI instance
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class AddressModel(BaseModel):
    city: str
    country: str

class StudentModel(BaseModel):
    name: str
    age: int
    address: AddressModel

class UpdateStudentModel(BaseModel):
    name: Optional[str]
    age: Optional[int]
    address: Optional[AddressModel]

def student_helper(student) -> dict:
    return {
        "id": str(student["_id"]),
        "name": student["name"],
        "age": student["age"],
        "address": {
            "city": student["address"]["city"],
            "country": student["address"]["country"],
        },
    }

def student_list_helper(students) -> list:
    return [student_helper(student) for student in students]


# Create Student
@app.post("/students", status_code=201)
def create_student(student: StudentModel):
    student_data = student.dict()
    result = student_collection.insert_one(student_data)
    return {"id": str(result.inserted_id)}

# List Students
@app.get("/students")
def list_students(
    country: Optional[str] = Query(None, description="Filter by country"),
    age: Optional[int] = Query(None, description="Filter by minimum age")
):
    filters = {}
    if country:
        filters["address.country"] = country
    if age:
        filters["age"] = {"$gte": age}
    students = list(student_collection.find(filters).limit(100))
    return {"data": student_list_helper(students)}

# Fetch Student by ID
@app.get("/students/{id}")
def fetch_student(id: str = Path(..., description="The ID of the student")):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    student = student_collection.find_one({"_id": ObjectId(id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_helper(student)

# Update Student
@app.patch("/students/{id}", status_code=204)
def update_student(
    id: str = Path(..., description="The ID of the student"),
    student: UpdateStudentModel = None
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    update_data = {k: v for k, v in student.dict(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = student_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {}

# Delete Student
@app.delete("/students/{id}", status_code=200)
def delete_student(id: str = Path(..., description="The ID of the student")):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    result = student_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}

# Run the API with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=10000, reload=True)
