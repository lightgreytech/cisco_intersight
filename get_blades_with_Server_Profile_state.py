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

    # Intersight operations, GET, POST, PATCH, DELETE
    OPERATIONS = [
        {
            "request_process": True,
            "resource_path": "equipment/DeviceSummaries",
            "request_method": "GET"
        },
    ]

    # Collect chassis details
    chassis_dict = {}

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
                all_devices = []

                # Prepare chassis dictionary
                for result in data.get("Results", []):
                    if "equipment.Chassis" in result.get("SourceObjectType", ""):
                        # chassis_dict[result.get("Moid")] = result.get("Moid")
                        chassis_dict = {
                            "Chassis_Moid": result.get("Moid"),
                            "Chassis_Model": result.get("Model"),
                            "Chassis_Serial": result.get("Serial")
                        }
                        # chassis_info = json.dumps(chassis_dict, indent=4)
                        # print (chassis_info)

                # Process compute blades
                for result in data.get("Results", []):
                    if result.get("SourceObjectType") == "compute.Blade":
                        device_entry = {
                            "Blade_Dn": result.get("Dn"),
                            "Blade_Model": result.get("Model"),
                            "Blade_Moid": result.get("Moid"),
                            "Blade_Serial": result.get("Serial"),
                            "Parent_Moid": result.get("Parent")["Moid"]
                        }
                        # Check if Service Profile is "Assigned"/"Associated" to the blade
                        blade_moid = device_entry["Blade_Moid"]
                        get_server_profiles = requests.get(BASE_URL + "server/Profiles",auth=AUTH)
                        all_server_profiles = get_server_profiles.json()

                        for server_profile in all_server_profiles.get("Results", []):
                            assigned_servers = server_profile.get("AssignedServer")
                            associated_servers = server_profile.get("AssociatedServer")
                            if assigned_servers:
                                for server in assigned_servers:
                                    assigned_moid = assigned_servers["Moid"]
                                    if blade_moid == assigned_moid:
                                        device_entry["Assigned_Server_Profile"] = server_profile.get("Name")
                                        if associated_servers:
                                            associated_moid = associated_servers["Moid"]
                                            if blade_moid in associated_moid:
                                                device_entry["Associated_to_a_profile"] = "TRUE!!!"+" 'Assigned' & 'Deployed'"
                                        else:
                                            device_entry["Associated_to_a_profile"] = "FALSE!!"+" 'Assigned' but NOT 'Deployed'"
                               
                        # Check if the blade's Moid is linked to a chassis Moid and append chassis model if available
                        parent_moid = result.get("Parent")["Moid"]
                        if parent_moid in chassis_dict["Chassis_Moid"]:
                            device_entry["Connected Chassis Model"] = chassis_dict["Chassis_Model"]
                            device_entry["Connected Chassis Serial"] = chassis_dict["Chassis_Serial"]
                            device_entry["Connected Chassis Moid"] = chassis_dict["Chassis_Moid"]
                         # check for Associated Service profiles

                        all_devices.append(device_entry)

                # Define the file path for the JSON file in the 'outputs' folder
                file_path = os.path.join(output_folder, "all_blades_and_service_profile_names.json")

                # Write the device summary data to the JSON file
                with open(file_path, 'w') as json_file:
                    json.dump(all_devices, json_file, indent=4)

                print(f"Blades and their corresponding Server Profiles have been written to {file_path}")
            else:
                print("Failed to retrieve Blades info.")
