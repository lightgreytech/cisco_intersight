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

                
                #GET Results list
                result_list = data.get("Results", [])
                # result_list = json.dumps(result_list, indent=4)
                # print (result_list)
                
                #ULTIMATE FOR-LOOP
                for result in result_list:
                    # #prepare FABRIC INTERCONNECTS dictionary
                    if "switch-" in result.get("Dn"):
                        fabric_interconnect_dict = {
                            "FI_Moid": result.get("Moid"),
                            "FI_Model": result.get("Model"),
                            "FI_Serial": result.get("Serial"),
                        }
                        # print(fabric_interconnect_dict)
                    # Prepare CHASSIS dictionary                   
                    if "equipment.Chassis" in result.get("SourceObjectType", ""):
                        chassis_dict = {
                            "Chassis_Moid": result.get("Moid"),
                            "Chassis_Model": result.get("Model"),
                            "Chassis_Serial": result.get("Serial"),
                        }
                    
                    server_type = result.get("SourceObjectType")
                    if server_type == "compute.Blade" or server_type == "compute.RackUnit":
                        device_entry = {
                            "Blade_Dn": result.get("Dn"),
                            "Blade_Model": result.get("Model"),
                            "Blade_Moid": result.get("Moid"),
                            "Blade_Serial": result.get("Serial"),
                            # "Parent_Moid": result.get("InventoryParent")["Moid"],
                        }
                        if "UCSC" in result.get("Model"):
                            device_entry["Server_Type"] = "This is a C-Series RACK Server"
                        elif "UCSX" in result.get("Model"):
                            device_entry["Server_Type"] = "This is an X-Series Server"
                        elif "UCSB" in result.get("Model"):
                            device_entry["Server_Type"] = "This is a B-Series Server"
                        else:
                            device_entry["Server_Type"] = "Not sure what Server Model this is!"
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
                        if server_type != "compute.RackUnit":    
                            parent_moid = result.get("InventoryParent")["Moid"]
                            
                            if parent_moid in chassis_dict["Chassis_Moid"]:
                                detail = {
                                    "Connected Chassis Model": chassis_dict["Chassis_Model"],
                                    "Connected Chassis Serial": chassis_dict["Chassis_Serial"],
                                    "Connected Chassis Moid": chassis_dict["Chassis_Moid"],
                                }
                                device_entry["Connected_Chassis_Info"] = detail
                                fi_moid = fabric_interconnect_dict["FI_Moid"]
                                # if fi_moid in 
                            
                        # device_entry = json.dumps(device_entry, indent=4)      
                        # print (device_entry)

                        all_devices.append(device_entry)
                # Define the file path for the JSON file in the 'outputs' folder
                    file_path = os.path.join(output_folder, "all_blades_and_service_profile_names.json")

                # Write the device summary data to the JSON file
                with open(file_path, 'w') as json_file:
                    json.dump(all_devices, json_file, indent=4)

                print(f"Blades and their corresponding Server Profiles have been written to {file_path}")
            else:
                print("Failed to retrieve Blades info.")