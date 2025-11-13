import os
import json
from dotenv import load_dotenv
from modrinth_uploader import update_project_summary, demote_latest_release, upload_modpack
from github_uploader import upload_to_github

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
    
    GAME_VERSIONS = config['version']['game_versions']
    VERSION_NUMBER = config['version']['number']
    LOADERS = config['version']['loaders']
    CHANGELOG = config['version']['changelog']
    FILE_PATH = config['version']['file_path'].replace('{VERSION_NUMBER}', VERSION_NUMBER)
    
    # --- Auto-Generated Fields ---
    VERSION_NAME = f"Always Updated v{VERSION_NUMBER} for Minecraft {GAME_VERSIONS[0]}"
    
    # --- Validation ---
    if not MODRINTH_TOKEN or not GITHUB_TOKEN:
        print("Please set your Modrinth and GitHub tokens in the .env file.")
        exit(1)
    
    # --- Main Upload Process ---
    modrinth_ok = False
    
    if update_project_summary(PROJECT_ID, GAME_VERSIONS, MODRINTH_TOKEN):
        if demote_latest_release(PROJECT_ID, MODRINTH_TOKEN):
            if upload_modpack(
                project_id=PROJECT_ID, 
                version_name=VERSION_NAME, 
                version_number=VERSION_NUMBER,
                changelog=CHANGELOG, 
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

    if modrinth_ok:
        if not upload_to_github(
            repo_owner=GITHUB_REPO_OWNER, 
            repo_name=GITHUB_REPO_NAME, 
            version_number=VERSION_NUMBER,
            version_name=VERSION_NAME, 
            changelog=CHANGELOG, 
            file_path=FILE_PATH, 
            github_token=GITHUB_TOKEN
        ):
            print("\nWARNING: Modrinth upload succeeded, but GitHub release failed.")
    
    print("\nScript finished.")