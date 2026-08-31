import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from curl_cffi import requests
from github import Github

# Load .env file from repository root or current directory
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Use Safari fingerprint to bypass Cloudflare. 
# Cloudflare aggressively flags Chrome fingerprints (DEFAULT_CHROME).
session = requests.Session(impersonate="safari17_0")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Env Vars
github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
repository = os.getenv('GITHUB_REPOSITORY')
endpoint_url = os.getenv('ENDPOINT_URL')
access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
bucket_name = os.getenv('BUCKET_NAME')

# APKmirror base url
base_url = "https://www.apkmirror.com"

if github_token:
    logging.info("GitHub token detected; using authenticated GitHub API client")
    gh = Github(github_token)
else:
    if os.getenv("CI"):
        logging.warning("No GITHUB_TOKEN detected in CI; GitHub release lookups may fail")
    else:
        logging.warning("No GitHub token detected; using anonymous GitHub API client")
    gh = Github()
