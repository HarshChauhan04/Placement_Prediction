"""
mongo_utils.py
==============
Purpose: Manage all interactions with MongoDB using PyMongo.
Author: Student Project (Explainable Machine Learning with MongoDB)

This module handles:
1. Connecting securely to a local MongoDB server with error verification.
2. Inserting records from the CSV file into a MongoDB database and collection.
3. Fetching documents from MongoDB back into a pandas DataFrame for ML.
4. Demonstrating essential NoSQL operations: find() query, aggregation pipeline, and update_one().
"""

import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables if available
load_dotenv()

# ==============================================================================
# NAMED CONSTANTS (No magic numbers)
# ==============================================================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")    # Standard local MongoDB port or Atlas URI
DATABASE_NAME = os.getenv("DATABASE_NAME", "placement_db")         # Dedicated database for this project
COLLECTION_NAME = "students"                                       # Collection storing student records
CONNECTION_TIMEOUT_MS = 3000                                       # 3 seconds timeout to quickly detect server downtime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_CSV_PATH = os.path.join(DATA_DIR, "placement_data.csv")


def get_mongo_client(uri=MONGO_URI, timeout_ms=CONNECTION_TIMEOUT_MS):
    """
    Establish and verify a connection to the MongoDB instance.

    Parameters:
        uri (str): The connection URI string (e.g. 'mongodb://localhost:27017').
        timeout_ms (int): Time to wait for server response before raising an error.

    Returns:
        MongoClient or None: A connected MongoClient object, or None if connection fails.
    """
    try:
        # We set serverSelectionTimeoutMS so the program does not hang if MongoDB is stopped
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)

        # Force a quick ping command to confirm the server is actually responding
        client.admin.command("ping")
        print(f"[mongo_utils.py] Successfully connected to MongoDB at {uri}")
        return client

    except (ConnectionFailure, ServerSelectionTimeoutError) as error:
        print("[mongo_utils.py] ERROR: Could not connect to MongoDB server!")
        print(f"                 Reason: {error}")
        print("                 Tip: Make sure the MongoDB service is running (e.g. 'net start MongoDB').")
        return None


def insert_csv_to_mongodb(csv_path=DEFAULT_CSV_PATH, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
    """
    Read the student CSV file and insert all records into the MongoDB collection.

    Parameters:
        csv_path (str): Filepath of the CSV to load.
        db_name (str): Name of the MongoDB database.
        collection_name (str): Name of the collection.

    Returns:
        int: Total number of documents inserted.
    """
    client = get_mongo_client()
    if client is None:
        raise ConnectionError("MongoDB is not available. Halting data insertion.")

    db = client[db_name]
    collection = db[collection_name]

    # Read CSV using pandas
    df = pd.read_csv(csv_path)

    # Convert DataFrame records into a list of Python dictionaries
    # Replace pandas NaN with None because MongoDB represents missing values as null (None in Python)
    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    # Drop existing documents so each run starts with clean data rather than stale duplicates
    collection.delete_many({})

    # Bulk insert all student documents into MongoDB
    insert_result = collection.insert_many(records)
    inserted_count = len(insert_result.inserted_ids)

    print(f"[mongo_utils.py] Inserted {inserted_count} student records into '{db_name}.{collection_name}'")
    client.close()
    return inserted_count


def fetch_data_from_mongodb(db_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
    """
    Fetch all student documents from MongoDB and return them as a pandas DataFrame.

    Parameters:
        db_name (str): Name of the database to read from.
        collection_name (str): Name of the collection to read from.

    Returns:
        pd.DataFrame: DataFrame containing all retrieved documents without the internal MongoDB '_id'.
    """
    client = get_mongo_client()
    if client is None:
        raise ConnectionError("MongoDB is not available. Halting data retrieval.")

    db = client[db_name]
    collection = db[collection_name]

    # Retrieve all documents; exclude '_id' because MongoDB's ObjectId is not needed by ML models
    cursor = collection.find({}, {"_id": 0})
    documents = list(cursor)

    df = pd.DataFrame(documents)
    print(f"[mongo_utils.py] Fetched {len(df)} documents from '{db_name}.{collection_name}' into DataFrame")
    client.close()
    return df


def find_high_performers_example(min_cgpa=8.5, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
    """
    Demonstrate a basic MongoDB find() query with filter criteria.

    Parameters:
        min_cgpa (float): The minimum CGPA threshold to query.
        db_name (str): Database name.
        collection_name (str): Collection name.

    Returns:
        list: A list of matching student documents (limited to top 5).
    """
    client = get_mongo_client()
    if client is None:
        return []

    collection = client[db_name][collection_name]

    # Filter query: students with CGPA >= min_cgpa who are placed
    query = {
        "cgpa": {"$gte": min_cgpa},
        "placed": 1
    }

    results = list(collection.find(query, {"_id": 0, "student_id": 1, "cgpa": 1, "branch": 1, "salary_lpa": 1}).limit(5))

    print(f"[mongo_utils.py] Demonstration of find(): Found {len(results)} sample placed students with CGPA >= {min_cgpa}:")
    for doc in results:
        print(f"                 - {doc['student_id']} | Branch: {doc['branch']} | CGPA: {doc['cgpa']} | Package: {doc['salary_lpa']} LPA")

    client.close()
    return results


def aggregate_salary_by_branch_example(db_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
    """
    Demonstrate MongoDB's aggregation pipeline to compute average salary and count by branch.

    Parameters:
        db_name (str): Database name.
        collection_name (str): Collection name.

    Returns:
        list: Aggregation results per engineering branch.
    """
    client = get_mongo_client()
    if client is None:
        return []

    collection = client[db_name][collection_name]

    # Aggregation Pipeline:
    # Stage 1 ($match): Only consider placed students with a valid salary value
    # Stage 2 ($group): Group by student branch, compute average salary and total count
    # Stage 3 ($sort): Sort from highest average package to lowest
    pipeline = [
        {"$match": {"placed": 1, "salary_lpa": {"$ne": None}}},
        {
            "$group": {
                "_id": "$branch",
                "average_salary_lpa": {"$avg": "$salary_lpa"},
                "placed_students_count": {"$sum": 1}
            }
        },
        {"$sort": {"average_salary_lpa": -1}}
    ]

    results = list(collection.aggregate(pipeline))

    print("[mongo_utils.py] Demonstration of aggregate(): Average Placed Package by Branch:")
    for row in results:
        avg_sal = round(row["average_salary_lpa"], 2)
        count = row["placed_students_count"]
        print(f"                 - {row['_id']:<24}: Avg Package: {avg_sal:>5.2f} LPA | Total Placed: {count}")

    client.close()
    return results


def update_student_record_example(student_id="STU1001", new_certifications=3, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
    """
    Demonstrate MongoDB update_one() to update a specific student's record.

    Parameters:
        student_id (str): The ID of the student to update.
        new_certifications (int): The new count of certifications.
        db_name (str): Database name.
        collection_name (str): Collection name.

    Returns:
        int: Number of documents modified (1 if successful, 0 otherwise).
    """
    client = get_mongo_client()
    if client is None:
        return 0

    collection = client[db_name][collection_name]

    # Use $set operator to update only the specified field without modifying other fields
    filter_query = {"student_id": student_id}
    update_data = {"$set": {"certifications": new_certifications}}

    result = collection.update_one(filter_query, update_data)
    print(f"[mongo_utils.py] Demonstration of update_one(): Updated {student_id} certifications to {new_certifications} (Modified count: {result.modified_count})")

    client.close()
    return result.modified_count


if __name__ == "__main__":
    print("--- STEP 2: MONGO UTILS DEMO ---")
    insert_csv_to_mongodb()
    df_fetched = fetch_data_from_mongodb()
    find_high_performers_example()
    aggregate_salary_by_branch_example()
    update_student_record_example()
