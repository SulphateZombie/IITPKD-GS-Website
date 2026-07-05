import os

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')

# Mapping from Google Sheets column names to clean MongoDB field names
FIELD_MAPPING = {
    "Name": "name",
    "Photo": "photo",
    "Subsystem": "subsystem",
    "Hierarchal position": "position",
    "Email ID": "email",
    "LinkedIN ID": "linkedin",
    "Instagram": "instagram",
    "Current Employer": "currentEmployer",
}

def _map_record(record: dict) -> dict:
    """Rename Google Sheets columns to clean MongoDB field names."""
    mapped = {}
    for key, value in record.items():
        mapped_key = FIELD_MAPPING.get(key, key)
        mapped[mapped_key] = value
    return mapped

def get_db(db_name='Members'):
    client = MongoClient(MONGO_URI)
    return client[db_name]

def sync_collections_from_sheets(unique_fields: dict = None):
    if unique_fields is None:
        unique_fields = {"members": "email", "alumni": "email"}

    from makedb import get_sheets_client, SPREADSHEET_CONFIG

    try:
        gc = get_sheets_client()
        db = get_db('Members')

        for sheet_id, config in SPREADSHEET_CONFIG.items():
            collection_name = config.get("collection")
            sheet_name = config.get("sheet_name")

            if not collection_name:
                continue

            print(f"Syncing collection '{collection_name}'...")

            try:
                spreadsheet = gc.open_by_key(sheet_id)
                if sheet_name:
                    worksheet = spreadsheet.worksheet(sheet_name)
                else:
                    worksheet = spreadsheet.sheet1

                records = worksheet.get_all_records()
                if not records:
                    print(f"  No data found in the {collection_name} spreadsheet.")
                    continue

                collection = db[collection_name]
                unique_field = unique_fields.get(collection_name, "email")
                operations = []

                for record in records:
                    mapped = _map_record(record)

                    # Upsert using the unique field (e.g., email) to match existing database entries
                    if unique_field in mapped:
                        filter_query = {unique_field: mapped[unique_field]}
                    else:
                        filter_query = mapped

                    operations.append(
                        UpdateOne(filter_query, {"$set": mapped}, upsert=True)
                    )

                if operations:
                    result = collection.bulk_write(operations)
                    print(f"  Sync complete for '{collection_name}'. Matched: {result.matched_count}, Modified: {result.modified_count}, "
                          f"Upserted (New): {result.upserted_count}")

            except Exception as e:
                print(f"  An error occurred while syncing collection '{collection_name}': {e}")

        return True

    except Exception as e:
        print(f"An error occurred during global sync: {e}")
        return False

def make_satellite(satellite_data: dict, project_data: dict):
    try:
        db = get_db("Projects")

        project_details = db["Project details"]
        sat = db["Satellites"]

        # 1. Insert the satellite details into the Satellites collection
        sat_result = sat.insert_one(satellite_data)

        # 2. Reference the generated ObjectId from the Satellite document
        project_data["projectData"] = sat_result.inserted_id
        project_data["projectType"] = "Satellite"

        # 3. Insert the linked project details into the Project details collection
        proj_result = project_details.insert_one(project_data)

        print(f"Successfully added Satellite! Satellite ID: {sat_result.inserted_id}, Project ID: {proj_result.inserted_id}")
        return True

    except Exception as e:
        print(f"  An error {e} occurred while syncing collection 'Satellites'.")
        return False

"""
```Example usage```
satellite_info = {
  "formFactor": "Form factor",
  "massGrams": "Weight in grams",
  "deployment": {"targetAltitudeMeters": "target", "ejectionMechanism": "Ejection Charge"},
  "recoverySystem": {"trackingMethod": "radio, gps", "successfullyRecovered": False},
  "powerSystem": {"batteryType": "Battery type", "capacityMAh": "capacity"},
  "instruments": ["some", "instruments"],
  "missionStatus": "Awaiting Launch",
  "googleDriveLinks": ["https://drive.google.com/link-to-image"]
}

project_info = {
  "projectName": "Project Name",
  "projectDescription": "Description",
  "projectLinks": ["https://drive.google.com/folder-link", "https://github.com/repo-link"]
}

make_satellite(satellite_info, project_info)
"""

def make_rocket(rocket_data: dict, project_data: dict):
    try:
        db = get_db("Projects")

        project_details = db["Project details"]
        rocket_col = db["Rockets"]

        # 1. Insert the Rocket details into the Rockets collection
        rocket_result = rocket_col.insert_one(rocket_data)

        # 2. Reference the generated ObjectId from the Rocket document
        project_data["projectData"] = rocket_result.inserted_id
        project_data["projectType"] = "Rocket"

        # 3. Insert the linked project details into the Project details collection
        proj_result = project_details.insert_one(project_data)

        print(f"Successfully added Rocket! Rocket ID: {rocket_result.inserted_id}, Project ID: {proj_result.inserted_id}")
        return True

    except Exception as e:
        print(f"  An error {e} occurred while syncing collection 'Rockets'.")
        return False

"""
```Example usage```
rocket_info = {
  "projectName": "Rocket name",
  "launchDate": datetime.datetime(y, m, d, h, min, sec, tzinfo=datetime.timezone.utc),
  "motorType": "Motor type",
  "altitude": {
    "target": "target",
    "actual": "actual",
    "unit": "m"
  },
  "payload": {
    "description": "payload description",
    "payloadData": ObjectId(id), # Linking to a satellite/payload id
    "weightGrams": "weight Grams"
  },
  "status": "Launched",
  "googleDriveLinks": [
    "https://drive.google.com/link-to-image"
  ]
}

project_info = {
  "projectName": "Project Name",
  "projectDescription": "Description",
  "projectLinks": ["https://drive.google.com/folder-link", "https://github.com/repo-link"]
}

make_rocket(rocket_info, project_info)
"""
