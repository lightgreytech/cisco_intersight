import requests
import json
import os

from keys import key_id
from intersight_auth import IntersightAuth

# Create an AUTH Object
AUTH = IntersightAuth(
    secret_key_filename='keys/key_secret.txt',
    api_key_id=key_id.API_KEY_ID
)

# Intersight REST API Base URL
BASE_URL = 'https://www.intersight.com/api/v1/'

if __name__ == "__main__":
    # Create the 'outputs' folder if it doesn't exist
    output_folder = 'outputs'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # intersight operations, GET, POST, PATCH, DELETE
    OPERATIONS = [
        {
            "request_process": True,
            "resource_path": "equipment/DeviceSummaries",
            "request_method": "GET"
        },
    ]

    for operation in OPERATIONS:
        if operation['request_process']:
            # GET
            if operation['request_method'] == "GET":
                response = requests.get(
                    BASE_URL + operation['resource_path'],
                    auth=AUTH
                )

            # Check if the response is successful
            if response and response.status_code == 200:
                data = response.json()
                all_fabric_interconnects = []
                for result in data.get("Results", []):
                    if "switch-" in result.get("Dn", ""):
                        all_fabric_interconnects.append({
                            "Dn": result.get("Dn"),
                            "Model": result.get("Model"),
                            "Moid": result.get("Moid"),
                            "Serial": result.get("Serial")
                        })

                # Define the file path for the JSON file in the 'outputs' folder
                file_path = os.path.join(output_folder, "fabric_interconnects.json")

                # Write the device summary data to the JSON file
                with open(file_path, 'w') as json_file:
                    json.dump(all_fabric_interconnects, json_file, indent=4)

                print(f"Device summary has been written to {file_path}")
            else:
                print("Failed to retrieve device summary.")
