import motor.motor_asyncio
from dotenv import load_dotenv
import os
load_dotenv()

USER = os.getenv("USER")
PASS = os.getenv("PASS")

MONGO_DETAILS = f"mongodb+srv://{USER}:{PASS}@cluster0.of5o4.mongodb.net/"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.student_management
student_collection = database.get_collection("students")

def student_helper(student) -> dict:
    return {
        "name": student["name"],
        "age": student["age"],
        "address": {
            "city": student["address"]["city"],
            "country": student["address"]["country"],
        },
    }

def student_list_helper(students) -> list:
    return [student_helper(student) for student in students]
