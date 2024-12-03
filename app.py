from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId
from database import student_collection, student_helper, student_list_helper
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

#CORS

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

@app.get("/")
async def home():
    return {"message": "Welcome to the Student Management System!"}

@app.get("/load-env")
async def load_env_var():
    mongo_string = os.getenv("MONGO_STRING")
    if not mongo_string:
        raise HTTPException(status_code=500, detail="MONGO_STRING environment variable is not set!")
    return {"MONGO_STRING": mongo_string}

# Create Student
@app.post("/students", status_code=201)
async def create_student(student: StudentModel):
    student_data = student.dict()
    result = await student_collection.insert_one(student_data)
    return {"id": str(result.inserted_id)}

# List Students
@app.get("/students")
async def list_students(
    country: Optional[str] = Query(None, description="Filter by country"),
    age: Optional[int] = Query(None, description="Filter by minimum age")
):
    filters = {}
    if country:
        filters["address.country"] = country
    if age:
        filters["age"] = {"$gte": age}
    students = await student_collection.find(filters).to_list(100)
    return {"data": student_list_helper(students)}

# Fetch Student by ID
@app.get("/students/{id}")
async def fetch_student(id: str = Path(..., description="The ID of the student")):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    student = await student_collection.find_one({"_id": ObjectId(id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_helper(student)

# Update Student
@app.patch("/students/{id}", status_code=204)
async def update_student(
    id: str = Path(..., description="The ID of the student"),
    student: UpdateStudentModel = None
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    update_data = {k: v for k, v in student.dict(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = await student_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {}

# Delete Student
@app.delete("/students/{id}", status_code=200)
async def delete_student(id: str = Path(..., description="The ID of the student")):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    result = await student_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}


# Run the API with uvicorn
# uvicorn app:app --reload



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app",host="0.0.0.0",port=10000,reload=True)