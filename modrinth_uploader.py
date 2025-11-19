import requests
import json
import os

def update_project_summary(project_id, desired_summary, modrinth_token):
    """
    Checks the project's summary on Modrinth and updates it only if it's different.
    Returns True on success, False on failure.
    """
    print("Checking Modrinth project summary...")
    
    api_url = f"https://api.modrinth.com/v2/project/{project_id}"
    headers = {"Authorization": modrinth_token, "User-Agent": "YoureIronic/Always-Updated (youreironic@duck.com)"}

    try:
        # --- STEP 1: GET the current project data ---
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        current_summary = response.json().get("description")

        # --- STEP 2: COMPARE the current summary with the desired one ---
        if current_summary == desired_summary:
            print("Project summary is already up-to-date. Skipping update.")

            print(f"[DEBUG] Current: {repr(current_summary)}")
            print(f"[DEBUG] Desired: {repr(desired_summary)}")

            return True

        # --- STEP 3: UPDATE only if they are different ---
        print("Project summary is outdated. Updating...")
        patch_data = {"description": desired_summary}
        patch_response = requests.patch(api_url, headers=headers, json=patch_data)
        patch_response.raise_for_status()
        
        print(f"Successfully updated Modrinth project summary.")
        return True

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error while checking/updating summary: {err}")
        print("Response body:", err.response.text)
        return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking/updating summary: {e}")
        return False

def demote_latest_release(project_id, modrinth_token):
    """
    Finds the latest "release" version of a project and changes it to "beta".
    """
    print("\nChecking for a previous Modrinth release to demote...")
    list_versions_url = f"https://api.modrinth.com/v2/project/{project_id}/version"
    headers = {"Authorization": modrinth_token, "User-Agent": "YoureIronic (youreironic@duck.com)"}
    try:
        response = requests.get(list_versions_url, headers=headers)
        response.raise_for_status()
        versions = response.json()
        latest_release = next((v for v in versions if v.get("version_type") == "release"), None)

        if not latest_release:
            print("No previous 'release' version found. Skipping demotion.")

            for v in versions[:3]:
                print(f"  Version: {v['version_number']}, type: {v['version_type']}")
            return True
        
        latest_release_id = latest_release["id"]
        latest_release_number = latest_release["version_number"]
        print(f"Found latest release: v{latest_release_number}. Demoting to 'beta'...")

        modify_url = f"https://api.modrinth.com/v2/version/{latest_release_id}"
        modify_response = requests.patch(modify_url, headers=headers, json={"version_type": "beta"})
        modify_response.raise_for_status()
        
        print(f"Successfully demoted v{latest_release_number} to 'beta'.")
        return True
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error during demotion: {err}\nResponse body: {err.response.text}")
        return False
    return True

def upload_modpack(project_id, version_name, version_number, changelog, game_versions, loaders, file_path, modrinth_token):
    """
    Uploads a new modpack version to a Modrinth project.
    """
    file_path = os.path.expanduser(file_path)
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return False
    
    print(f"\nUploading new release to Modrinth: {version_name}...")
    api_url = "https://api.modrinth.com/v2/version"
    headers = {"Authorization": modrinth_token, "User-Agent": "YoureIronic (youreironic@duck.com)"}
    data = {
        "project_id": project_id, "name": version_name, "version_number": version_number,
        "changelog": changelog, "game_versions": game_versions, "loaders": loaders,
        "version_type": "release", "featured": True, "status": "listed",
        "dependencies": [], "file_parts": ["file"]
    }
    files = {"file": (os.path.basename(file_path), open(file_path, "rb"), "application/x-modrinth-modpack+zip")}
    form_data = {'data': json.dumps(data)}
    try:
        response = requests.post(api_url, headers=headers, data=form_data, files=files)
        response.raise_for_status()
        print("Modpack uploaded to Modrinth successfully!")
        return True
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error during Modrinth upload: {err}\nResponse body: {err.response.text}")
        return False
    finally:
        if 'file' in files:
            files['file'][1].close()