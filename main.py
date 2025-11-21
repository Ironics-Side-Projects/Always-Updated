import os
import json
from dotenv import load_dotenv
from modrinth_uploader import update_project_summary, demote_latest_release, upload_modpack
from github_uploader import upload_to_github, update_github_repo_description

# Load environment variables
load_dotenv()

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

if __name__ == "__main__":
    # --- Get Tokens from Environment ---
    MODRINTH_TOKEN = os.getenv('MODRINTH_TOKEN')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # --- Get Configuration ---
    PROJECT_ID = config['project']['modrinth_id']
    GITHUB_REPO_OWNER = config['project']['github_repo_owner']
    GITHUB_REPO_NAME = config['project']['github_repo_name']
    PROJECT_SUMMARY = config['project']['project_summary']
    
    GAME_VERSIONS = config['version']['game_versions']
    VERSION_NUMBER = config['version']['number']
    LOADERS = config['version']['loaders']
    BASE_CHANGELOG = config['version']['changelog'].rstrip()  # Normalize: remove trailing whitespace
    
    FILE_PATH = config['version']['file_path'].replace('{VERSION_NUMBER}', VERSION_NUMBER)
    
    # --- Auto-Generated Fields ---
    VERSION_NAME = f"Always Updated v{VERSION_NUMBER} for Minecraft {GAME_VERSIONS[0]}"

    # --- Generate Platform-Specific Changelogs ---
    MODRINTH_DOWNLOAD_URL = f"https://modrinth.com/modpack/always-updated/version/{VERSION_NUMBER}"
    GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/tag/v{VERSION_NUMBER}"

    CHANGELOG_FOR_MODRINTH = f"""{BASE_CHANGELOG}

Get on GitHub: [Download Here]({GITHUB_RELEASE_URL})"""

    CHANGELOG_FOR_GITHUB = f"""{BASE_CHANGELOG}

Get on Modrinth: [Download Here]({MODRINTH_DOWNLOAD_URL})"""
    
    # --- Validation ---
    if not MODRINTH_TOKEN or not GITHUB_TOKEN:
        print("Please set your Modrinth and GitHub tokens in the .env file.")
        exit(1)
    
    # --- Main Upload Process ---
    modrinth_ok = False
    
    if update_project_summary(PROJECT_ID, PROJECT_SUMMARY, MODRINTH_TOKEN):
        if demote_latest_release(PROJECT_ID, MODRINTH_TOKEN):
            if upload_modpack(
                project_id=PROJECT_ID, 
                version_name=VERSION_NAME, 
                version_number=VERSION_NUMBER,
                changelog=CHANGELOG_FOR_MODRINTH,  # 👈 Uses Modrinth-tailored changelog
                game_versions=GAME_VERSIONS, 
                loaders=LOADERS,
                file_path=FILE_PATH, 
                modrinth_token=MODRINTH_TOKEN
            ):
                modrinth_ok = True
            else:
                print("\nUpload halted because the new version could not be uploaded to Modrinth.")
        else:
            print("\nUpload halted because the previous Modrinth version could not be demoted.")
    else:
        print("\nProcess halted because the Modrinth project summary could not be updated.")

    # --- Sync GitHub repo description & create release if Modrinth succeeded ---
    if modrinth_ok:
        # First, update the GitHub repo's main description to match Modrinth
        if not update_github_repo_description(
            repo_owner=GITHUB_REPO_OWNER,
            repo_name=GITHUB_REPO_NAME,
            new_description=PROJECT_SUMMARY,
            github_token=GITHUB_TOKEN
        ):
            print("\nWARNING: Modrinth upload succeeded, but GitHub repo description update failed.")
        
        # Then, create the GitHub release and upload the asset
        if not upload_to_github(
            repo_owner=GITHUB_REPO_OWNER, 
            repo_name=GITHUB_REPO_NAME, 
            version_number=VERSION_NUMBER,
            version_name=VERSION_NAME, 
            changelog=CHANGELOG_FOR_GITHUB,  # 👈 Uses GitHub-tailored changelog
            file_path=FILE_PATH, 
            github_token=GITHUB_TOKEN
        ):
            print("\nWARNING: Modrinth upload succeeded, but GitHub release failed.")
    
    print("\nScript finished.")