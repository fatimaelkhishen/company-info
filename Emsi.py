# emsi.py
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()
logging.getLogger('urllib3').setLevel(logging.WARNING)

# ==========================
# EMSI Credentials
# ==========================
EMSI_USER = "un-escwa"
EMSI_SECRET = "Ol9ckkjVy3RnbFZY"
TOKEN = ""

# ==========================
# EMSI Authentication
# ==========================
def get_auth() -> str:
    """Obtain EMSI authentication token."""
    global TOKEN
    url = "https://auth.emsicloud.com/connect/token"
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    payload = f"grant_type=client_credentials&client_id={EMSI_USER}&client_secret={EMSI_SECRET}"
    try:
        response = requests.post(url, data=payload, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token", "")
        if not access_token:
            raise ValueError("No access_token in EMSI response")
        TOKEN = access_token
        return TOKEN
    except Exception as e:
        logger.error(f"Failed to get EMSI token: {e}")
        return ""

def is_valid_token() -> bool:
    """Check if current EMSI token is valid."""
    global TOKEN
    if not TOKEN:
        return False
    url = "https://emsiservices.com/skills/status"
    headers = {'authorization': f'Bearer {TOKEN}'}
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        return response.ok
    except Exception:
        return False

# ==========================
# Skill Extraction
# ==========================
def extract_skills(skill_object: dict) -> list:
    """Extract skills with confidence > 0.8 from EMSI response."""
    if not isinstance(skill_object, dict) or "data" not in skill_object:
        logger.warning(f"Unexpected EMSI response: {skill_object}")
        return []
    skills = skill_object["data"]
    extracted = [
        {
            "Name": s["skill"]["name"],
            "Type": s["skill"]["type"],
            "Confidence": s["confidence"]
        }
        for s in skills if s.get("confidence", 0) > 0.8
    ]
    return extracted

def get_skills(text: str) -> list:
    """Call EMSI API and return list of skill dictionaries."""
    global TOKEN
    if not text or not text.strip():
        return []

    if not is_valid_token():
        TOKEN = get_auth()
        if not TOKEN:
            logger.error("Unable to obtain valid EMSI token.")
            return []

    url = "https://emsiservices.com/skills/versions/9.1/extract"
    headers = {
        'authorization': f'Bearer {TOKEN}',
        'content-type': 'application/json'
    }
    payload = {"text": text, "confidenceThreshold": 0.8}
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=20)
        if response.status_code != 200:
            logger.warning(f"EMSI API error {response.status_code}: {response.text[:200]}")
            return []
        return extract_skills(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []
    except ValueError:
        logger.error("Invalid JSON response.")
        return []

def extract_names(skill_list: list, skill_type: str) -> str:
    """Extract skill names of a given type ('ST1' = Hard, 'ST2' = Soft)."""
    if not isinstance(skill_list, list):
        return ""
    names = [
        item.get("Name", "")
        for item in skill_list
        if isinstance(item, dict) and isinstance(item.get("Type"), dict) and item["Type"].get("id") == skill_type
    ]
    return ", ".join(name for name in names if name)

def extract_skills_from_text(text: str) -> dict:
    """Return dict with hard and soft skills from text."""
    skills = get_skills(text)
    hard_skills = extract_names(skills, "ST1")
    soft_skills = extract_names(skills, "ST2")
    return {"hard_skills": hard_skills, "soft_skills": soft_skills}
