import requests
import json
import os

# ==============================================================================
# GITHUB UPLOADER FUNCTION
# ==============================================================================
def upload_to_github(repo_owner, repo_name, version_number, version_name, changelog, file_path, github_token):
    """
    Creates a new release on GitHub and uploads the modpack file as a release asset.
    Returns True on success, False on failure.
    """
    print("\nStarting GitHub release process...")
    file_path = os.path.expanduser(file_path)
    if not os.path.exists(file_path):
        print(f"Error: GitHub upload failed because file does not exist: '{file_path}'")
        return False

    tag_name = f"v{version_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    release_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    release_data = {
        "tag_name": tag_name,
        "name": version_name,
        "body": changelog,
        "draft": False,
        "prerelease": False
    }

    try:
        print(f"Creating GitHub release for tag {tag_name}...")
        response = requests.post(release_api_url, headers=headers, json=release_data)
        response.raise_for_status()
        release_info = response.json()
        upload_url = release_info["upload_url"]
        print("GitHub release created successfully.")

        asset_upload_url = upload_url.split('{')[0] + f"?name={os.path.basename(file_path)}"
        asset_headers = {
            "Authorization": f"token {github_token}",
            "Content-Type": "application/octet-stream"
        }

        print(f"Uploading '{os.path.basename(file_path)}' to GitHub release...")
        with open(file_path, 'rb') as file_data:
            upload_response = requests.post(asset_upload_url, headers=asset_headers, data=file_data)
            upload_response.raise_for_status()
        
        print("Asset uploaded to GitHub successfully.")
        return True

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error during GitHub process: {err}")
        print("Response body:", err.response.text)
        return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during GitHub process: {e}")
        return False

# ==============================================================================
# MODRINTH UPLOADER FUNCTION
# ==============================================================================

def update_project_summary(project_id, game_versions, modrinth_token):
    """
    Checks the project's summary on Modrinth and updates it only if it's different.
    Returns True on success, False on failure.
    """
    print("Checking Modrinth project summary...")
    if not game_versions:
        print("Error: GAME_VERSIONS list is empty. Cannot update summary.")
        return False

    desired_summary = f"[{game_versions[0]} / 1.21.11] - Modpack that mainly tries to support snapshots with maximum performance."
    
    api_url = f"https://api.modrinth.com/v2/project/{project_id}"
    headers = {"Authorization": modrinth_token, "User-Agent": "YoureIronic (youreironic@duck.com)"}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        current_summary = response.json().get("description")

        if current_summary == desired_summary:
            print("Project summary is already up-to-date. Skipping update.")
            return True

        print("Project summary is outdated. Updating...")
        patch_data = {"description": desired_summary}
        patch_response = requests.patch(api_url, headers=headers, json=patch_data)
        patch_response.raise_for_status()
        
        print(f"Successfully updated project summary.")
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

# ==============================================================================
# MAIN EXECUTION & CONFIGURATION
# ==============================================================================

if __name__ == "__main__":
    # --- Configuration ---
    MODRINTH_TOKEN = ""
    GITHUB_TOKEN = ""
    
    # --- Project & Repo Details ---
    PROJECT_ID = "drZrp9Uv"
    GITHUB_REPO_OWNER = "Ironics-Side-Projects"
    GITHUB_REPO_NAME = "Always-Updated"

    # --- Version Specifics ---
    GAME_VERSIONS = ["25w43a"]
    VERSION_NUMBER = "3.4.2"
    FILE_PATH = f"~/Downloads/Always Updated {VERSION_NUMBER}.mrpack"
    
    # --- Auto-Generated Fields ---
    VERSION_NAME = f"Always Updated v{VERSION_NUMBER} for Minecraft {GAME_VERSIONS[0]}"
    CHANGELOG = f"- Added [kennytvs-epic-force-close-loading-screen-mod-for-fabric](https://modrinth.com/mod/forcecloseworldloadingscreen)"
    LOADERS = ["fabric"]

    # --- End of Configuration ---

    # --- Validation ---
    if "YOUR_MODRINTH_TOKEN" in MODRINTH_TOKEN or "YOUR_GITHUB_TOKEN" in GITHUB_TOKEN:
        print("Please set your Modrinth and GitHub tokens in the script.")
    else:
        modrinth_ok = False
        if update_project_summary(PROJECT_ID, GAME_VERSIONS, MODRINTH_TOKEN):
            if demote_latest_release(PROJECT_ID, MODRINTH_TOKEN):
                if upload_modpack(
                    project_id=PROJECT_ID, version_name=VERSION_NAME, version_number=VERSION_NUMBER,
                    changelog=CHANGELOG, game_versions=GAME_VERSIONS, loaders=LOADERS,
                    file_path=FILE_PATH, modrinth_token=MODRINTH_TOKEN
                ):
                    modrinth_ok = True
                else:
                    print("\nUpload halted because the new version could not be uploaded to Modrinth.")
            else:
                print("\nUpload halted because the previous Modrinth version could not be demoted.")
        else:
            print("\nProcess halted because the Modrinth project summary could not be updated.")

        if modrinth_ok:
            if not upload_to_github(
                repo_owner=GITHUB_REPO_OWNER, repo_name=GITHUB_REPO_NAME, version_number=VERSION_NUMBER,
                version_name=VERSION_NAME, changelog=CHANGELOG, file_path=FILE_PATH, github_token=GITHUB_TOKEN
            ):
                print("\nWARNING: Modrinth upload succeeded, but GitHub release failed.")
        
        print("\nScript finished.")
