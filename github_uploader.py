import requests
import os

def update_github_repo_description(repo_owner, repo_name, new_description, github_token):
    """
    Updates the GitHub repository's description.
    Returns True on success, False on failure.
    """
    print(f"\nUpdating GitHub repository description for {repo_owner}/{repo_name}...")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = {
        "description": new_description
    }

    try:
        response = requests.patch(api_url, headers=headers, json=data)
        response.raise_for_status()
        print("GitHub repository description updated successfully.")
        return True
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error while updating GitHub repo description: {err}")
        print("Response body:", err.response.text)
        return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while updating GitHub repo description: {e}")
        return False

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

    # --- Step 1: Create the Release ---
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

        # --- Step 2: Upload the .mrpack file as a release asset ---
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