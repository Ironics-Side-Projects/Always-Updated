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
    data = {"description": new_description}

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

def get_unique_tag(repo_owner, repo_name, base_version, github_token):
    """
    Finds a unique tag name by checking existing tags and appending a suffix if needed.
    Returns (unique_tag, suffix) where suffix is 0 if no deduplication was needed.
    """
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    base_tag = f"v{base_version}"
    
    # Check if base tag exists
    check_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/tags/{base_tag}"
    response = requests.get(check_url, headers=headers)
    
    if response.status_code == 404:
        return base_tag, 0
    
    # Tag exists - find unique suffix by listing all tags
    print(f"Tag {base_tag} already exists. Finding unique suffix...")
    
    tags_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/tags"
    response = requests.get(tags_url, headers=headers)
    
    if response.status_code == 404:
        # No tags exist at all (shouldn't happen if base_tag check passed, but handle anyway)
        return base_tag, 0
    
    response.raise_for_status()
    existing_tags = {ref["ref"].replace("refs/tags/", "") for ref in response.json()}
    
    # Find the next available suffix
    suffix = 1
    while True:
        candidate_tag = f"{base_tag}-{suffix}"
        if candidate_tag not in existing_tags:
            print(f"Using unique tag: {candidate_tag}")
            return candidate_tag, suffix
        suffix += 1
        if suffix > 1000:  # Safety limit
            raise Exception(f"Too many versions with base version {base_version}")

def upload_to_github(repo_owner, repo_name, version_number, version_name, changelog, file_path, github_token):
    """
    Creates a new release on GitHub with a unique tag and uploads the modpack file as a release asset.
    Returns True on success, False on failure.
    """
    print("\nStarting GitHub release process...")
    file_path = os.path.expanduser(file_path)
    if not os.path.exists(file_path):
        print(f"Error: GitHub upload failed because file does not exist: '{file_path}'")
        return False

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # Get a unique tag name
        tag_name, suffix = get_unique_tag(repo_owner, repo_name, version_number, github_token)
        
        # Update version name if we had to add a suffix
        if suffix > 0:
            release_name = f"{version_name} ({suffix})"
        else:
            release_name = version_name

        release_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
        release_data = {
            "tag_name": tag_name,
            "name": release_name,
            "body": changelog,
            "draft": False,
            "prerelease": False
        }

        print(f"Creating GitHub release with tag {tag_name}...")
        response = requests.post(release_api_url, headers=headers, json=release_data)
        response.raise_for_status()
        release_info = response.json()
        upload_url = release_info["upload_url"]
        print(f"GitHub release created: {release_info.get('html_url', 'N/A')}")

        # --- Upload the .mrpack file as a release asset ---
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