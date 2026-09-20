import os
import io
import json
import traceback
import pdfplumber

from dotenv import load_dotenv
from google import genai
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime
import re

from secure_processing import (
    get_secure_provider,
    process_sensitive_data,
    secure_inference,
    get_security_status,
    get_attestation_report,
    audit_logger,
    rate_limit_sensitive,
    apply_security_headers,
    validate_pdf_stream
)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"

# =====================================================
# Load Environment Variables
# =====================================================

load_dotenv()
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "static", "data", "countries_currency.json")
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        COUNTRY_CURRENCY = json.load(f)
else:
    COUNTRY_CURRENCY = {}

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
client = None

def get_gemini_client():
    global client, API_KEY
    if client is not None:
        return client
    API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in server environment variables.")
    client = genai.Client(api_key=API_KEY)
    return client

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini API Loaded Successfully")
    except Exception as e:
        print(f"Notice: Gemini client init deferred: {e}")
else:
    print("[WARNING] GEMINI_API_KEY not set in environment variables. Web app is running; AI features will require GEMINI_API_KEY.")

# =====================================================
# Gemini Model Fallback System
# =====================================================

GEMINI_MODELS = [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]


def get_active_models():
    models = list(GEMINI_MODELS)
    try:
        active_client = get_gemini_client()
        remote_models = [m.name.replace("models/", "") for m in active_client.models.list()]
        exclude = ['tts', 'image', 'imagen', 'veo', 'lyria', 'embedding', 'audio', 'robotics', 'banana', 'aqa', 'computer-use', 'live-translate']
        filtered = [m for m in remote_models if not any(x in m for x in exclude)]
        for m in reversed(filtered):
            if m not in models:
                models.insert(0, m)
    except Exception as e:
        print(f"Note: Could not fetch dynamic models list: {e}")
    return models


def generate_with_fallback(prompt):
    active_client = get_gemini_client()
    models_to_try = get_active_models()
    last_error = None

    for model in models_to_try:
        try:
            print(f"Trying Gemini model: {model}")
            response = active_client.models.generate_content(
                model=model,
                contents=prompt
            )
            if response and hasattr(response, 'text') and response.text:
                print(f"[SUCCESS] Generated content using model: {model}")
                return response.text.strip()
        except Exception as e:
            print(f"[FAILED] Model {model} failed: {str(e)[:100]}")
            last_error = e
            continue

    raise Exception(f"All Gemini models failed.\n{last_error}")


# =====================================================
# Flask Configuration & Secret Key
# =====================================================

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "careerverse_secure_session_secret_key_2026")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB maximum upload limit

@app.errorhandler(413)
def request_entity_too_large(error):
    audit_logger.log_event("UPLOAD_EXCEEDED_MAX_SIZE", "BLOCKED", level=30)
    return failure("Uploaded file is too large. Maximum allowed size is 10MB.", 413)

@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return apply_security_headers(response)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =====================================================
# Helper Functions
# =====================================================

def clean_json(text):
    if not text:
        return "{}"
    text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0).strip()
    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    if text.startswith("```"):
        text = text.replace("```", "", 1)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def success(data):
    data["success"] = True
    return jsonify(data)


def failure(message, code=500):
    return jsonify({
        "success": False,
        "error": message
    }), code

VALID_ACRONYMS = {
    "ai", "ml", "ui", "ux", "hr", "pr", "it", "qa", "seo", "sre", "cto", "ceo", "cfo", "vp", "dba", "erp", "crm", "bi", "ar", "vr", "3d", "2d", "5g", "cad", "gis", "pm", "dev", "ops", "sec", "mlops", "devops", "secops", "web3", "web2", "ios", "nlp", "llm", "genai", "ar/vr", "ui/ux", "ai/ml", "c++", "c#", ".net",
    # Competitive Exams & Entrance Acronyms
    "neet", "jee", "gate", "cat", "usmle", "plab", "nclex", "gmat", "gre", "sat", "act", "ielts", "toefl", "medical", "doctor", "nursing", "paramedical",
    # Medical & Health Acronyms
    "mbbs", "bds", "bams", "bhms", "bpt", "mch", "dnb", "bums", "brms", "md", "ms", "frcs", "mrcp", "mrcs", "pharmd", "gnm", "anm",
    # Law & Judicial Acronyms
    "llb", "llm", "bcl", "aibe", "clat",
    # Civil Services, Defense & Public Acronyms
    "ias", "ips", "ifs", "irs", "upsc", "nda", "cds", "afcat", "ssc", "psc", "gpsc", "mpsc", "uppsc", "bpsc", "chsl", "wbcs", "jkpsc", "tnpsc", "tspsc", "cgpsc", "hpsc", "kpsc", "ppsc", "mppsc", "rrb", "isro", "drdo", "barc", "hal", "bel", "gail", "ntpc",
    # Aviation Acronyms
    "cpl", "atpl", "ppl", "dgca", "faa",
    # Business, Finance & Accounting Acronyms
    "ca", "cfa", "cpa", "cfp", "cma", "acca", "cs", "frm",
    # Higher Education Degrees
    "btech", "mtech", "bca", "mca", "bba", "mba", "bsc", "msc", "phd", "bed", "med", "bdes", "mdes", "barch", "march"
}

QWERTY_PATTERNS = [
    "qwertyuiop", "poiuytrewq", "asdfghjkl", "lkjhgfdsa", "zxcvbnm", "mnbvcxz",
    "qazwsx", "edcrfv", "tgbnhy", "ujmiko", "olp", "zaq", "xsw", "cde", "vfr", "bgt", "nhy", "mju", "lki", "plo",
    "1234567890", "0987654321"
]

COMMON_TYPO_MAP = {
    "softwere": "software",
    "softweare": "software",
    "softwaer": "software",
    "scintist": "scientist",
    "scintific": "scientific",
    "machanical": "mechanical",
    "mechenical": "mechanical",
    "fasion": "fashion",
    "fassion": "fashion",
    "enginier": "engineer",
    "enginer": "engineer",
    "engneer": "engineer",
    "engeneer": "engineer",
    "devloper": "developer",
    "developper": "developer",
    "devoloper": "developer",
    "artifical": "artificial",
    "intelegence": "intelligence",
    "inteligence": "intelligence",
    "machne": "machine",
    "aerospase": "aerospace",
    "docter": "doctor",
    "physican": "physician",
    "aeronaotical": "aeronautical",
    "pyton": "python",
    "cybersecuity": "cybersecurity",
    "cybersecurty": "cybersecurity",
    "analist": "analyst",
    "maneger": "manager",
    "archtect": "architect",
    "profeser": "professor",
    "profesor": "professor",
    "elecrician": "electrician",
    "plubmer": "plumber",
    "jornalist": "journalist",
    "acountant": "accountant",
    "lawer": "lawyer"
}

KNOWN_ORGANIZATIONS = {
    "nasa", "isro", "drdo", "barc", "hal", "bel", "spacex", "blue origin", "esa", "cern",
    "google", "microsoft", "apple", "amazon", "meta", "netflix", "tesla", "nvidia", "openai", "deepmind",
    "ibm", "intel", "oracle", "cisco", "tcs", "infosys", "wipro", "hcl", "accenture", "deloitte",
    "mckinsey", "bcg", "bain", "goldman sachs", "jpmorgan", "morgan stanley", "un", "who", "world bank"
}

KNOWN_BROAD_FIELDS = {
    "fashion", "finance", "healthcare", "health", "medicine", "law", "agriculture", "farming",
    "architecture", "aviation", "cybersecurity", "cyber security", "artificial intelligence",
    "machine learning", "data science", "space science", "space", "astronomy", "animation",
    "vfx", "gaming", "game development", "game design", "marketing", "digital marketing",
    "biotechnology", "biotech", "nanotechnology", "robotics", "devops", "cloud computing",
    "journalism", "media", "entertainment", "music", "cinema", "filmmaking", "sports",
    "civil services", "defence", "defense", "military", "education", "teaching", "real estate",
    "hospitality", "culinary arts", "logistics", "supply chain", "renewable energy"
}

KNOWN_PLACEHOLDERS = {
    "test", "testing", "tester", "none", "null", "unknown", "n/a", "na", "sample", "temp",
    "xyz", "abc", "asdf", "qwerty", "placeholder", "demo", "dummy", "nothing", "anything",
    "fake", "blah", "random", "job", "career", "work", "role"
}

def is_qwerty_mashing(text):
    clean = re.sub(r'[^a-z0-9]', '', text.lower())
    if len(clean) < 3:
        return False
    for i in range(len(clean) - 3):
        sub = clean[i:i+4]
        if any(sub in pattern for pattern in QWERTY_PATTERNS):
            return True
    return False

def validate_career_universal(career_input):
    if not career_input or not str(career_input).strip():
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    raw = str(career_input).strip()
    clean = raw.lower()

    # 1. Reject if no letters or numbers
    if not re.search(r'[a-zA-Z0-9]', clean):
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    # 2. Reject symbol spam / invalid punctuation
    if re.search(r'[@$%^*~`_={}\[\]|\\<>;:"]', clean):
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    # 3. Reject pure numbers
    if re.match(r'^\d+$', clean):
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    # 4. Reject length out of reasonable range
    if len(clean) < 2 or len(clean) > 80:
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    # 5. Reject exact placeholder/test inputs
    if clean in KNOWN_PLACEHOLDERS:
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    # 6. Reject QWERTY / keyboard mashing & keyboard walks
    if is_qwerty_mashing(clean):
        return {
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Please enter a valid career, job role, profession, or career field."
        }

    # 7. Reject meaningless alphanumeric combos (e.g. abc123xyz, 123abc456)
    if re.match(r'^[a-z0-9]{5,}$', clean) and re.search(r'\d', clean) and re.search(r'[a-z]', clean):
        if clean not in ["web3", "web2", "3d", "2d", "5g", "4g", "b2b", "b2c"]:
            return {
                "valid": False,
                "normalized_input": None,
                "input_type": "invalid",
                "error": "Please enter a valid career, job role, profession, or career field."
            }

    # 8. Reject vowel-less gibberish (unless standard known acronyms)
    alpha_only = re.sub(r'[^a-z]', '', clean)
    if len(alpha_only) >= 4 and not any(v in alpha_only for v in "aeiouy"):
        if alpha_only not in VALID_ACRONYMS:
            return {
                "valid": False,
                "normalized_input": None,
                "input_type": "invalid",
                "error": "Please enter a valid career, job role, profession, or career field."
            }

    # 9. Reject unnatural consonant clusters / gibberish patterns (e.g. hfuy, jsdh, zxcv, qwrty)
    words_to_check = clean.split()
    for w in words_to_check:
        if w in VALID_ACRONYMS:
            continue
        unnatural_patterns = [
            r'[bcdfghjklmnpqrstvwxz]{5,}',
            r'^[bcdfghjklmnpqrstvwxz]{4,}',
            r'^[qwertyuiop]{6,}$',
            r'^[asdfghjkl]{5,}$',
            r'^[zxcvbnm]{4,}$',
            r'(.)\1{3,}'  # 4+ repeated chars e.g. aaaa, zzzz
        ]
        for pat in unnatural_patterns:
            if re.search(pat, w):
                return {
                    "valid": False,
                    "normalized_input": None,
                    "input_type": "invalid",
                    "error": "Please enter a valid career, job role, profession, or career field."
                }

    # 10. Check specific random gibberish (e.g. hfuyaw, jsdhfks)
    gibberish_subs = ["hfuy", "uyaw", "jsdh", "hfks", "asdf", "dfgh", "ghjk", "jkl;", "zxcv", "xcvb", "cvbn", "vbnm", "qwer", "wert", "erty", "rtyu", "tyui", "yuio", "uiop"]
    for w in words_to_check:
        if w in VALID_ACRONYMS:
            continue
        if any(sub in w for sub in gibberish_subs):
            return {
                "valid": False,
                "normalized_input": None,
                "input_type": "invalid",
                "error": "Please enter a valid career, job role, profession, or career field."
            }

    # 11. Minor typo correction
    words = clean.split()
    corrected_words = []
    for w in words:
        corrected_words.append(COMMON_TYPO_MAP.get(w, w))
    normalized_str = " ".join(corrected_words).title()

    # Special handling for known acronyms in title
    norm_tokens = normalized_str.split()
    final_tokens = []
    for tok in norm_tokens:
        tok_l = tok.lower()
        if tok_l in VALID_ACRONYMS or tok_l in KNOWN_ORGANIZATIONS:
            final_tokens.append(tok.upper())
        else:
            final_tokens.append(tok)
    normalized_name = " ".join(final_tokens)

    # 12. Classify input_type
    clean_norm = normalized_name.lower()
    
    # Organization-only (e.g. NASA, ISRO, DRDO)
    if clean_norm in KNOWN_ORGANIZATIONS:
        return {
            "valid": True,
            "normalized_input": normalized_name,
            "input_type": "organization_career",
            "error": None
        }

    # Organization-specific career (e.g. NASA Aerospace Engineer, ISRO Scientist)
    if any(clean_norm.startswith(org + " ") or (" " + org + " ") in clean_norm for org in KNOWN_ORGANIZATIONS):
        return {
            "valid": True,
            "normalized_input": normalized_name,
            "input_type": "organization_career",
            "error": None
        }

    # Broad professional fields
    if clean_norm in KNOWN_BROAD_FIELDS:
        return {
            "valid": True,
            "normalized_input": normalized_name,
            "input_type": "broad_field",
            "error": None
        }

    # Specific real-world careers
    return {
        "valid": True,
        "normalized_input": normalized_name,
        "input_type": "specific_role",
        "error": None
    }

def validate_career_input(career):
    res = validate_career_universal(career)
    if not res["valid"]:
        return False, res["error"]
    return True, res["normalized_input"]

REAL_WORLD_COUNTRIES = {
    "afghanistan", "albania", "algeria", "andorra", "angola", "antigua and barbuda", "argentina", "armenia",
    "australia", "austria", "azerbaijan", "bahamas", "bahrain", "bangladesh", "barbados", "belarus",
    "belgium", "belize", "benin", "bhutan", "bolivia", "bosnia and herzegovina", "botswana", "brazil",
    "brunei", "bulgaria", "burkina faso", "burundi", "cambodia", "cameroon", "canada", "cape verde",
    "central african republic", "chad", "chile", "china", "colombia", "comoros", "congo", "costa rica",
    "croatia", "cuba", "cyprus", "czech republic", "czechia", "denmark", "djibouti", "dominica",
    "dominican republic", "ecuador", "egypt", "el salvador", "equatorial guinea", "eritrea", "estonia",
    "eswatini", "ethiopia", "fiji", "finland", "france", "gabon", "gambia", "georgia", "germany",
    "ghana", "greece", "grenada", "guatemala", "guinea", "guinea-bissau", "guyana", "haiti", "honduras",
    "hungary", "iceland", "india", "indonesia", "iran", "iraq", "ireland", "israel", "italy",
    "jamaica", "japan", "jordan", "kazakhstan", "kenya", "kiribati", "kuwait", "kyrgyzstan", "laos",
    "latvia", "lebanon", "lesotho", "liberia", "libya", "liechtenstein", "lithuania", "luxembourg",
    "madagascar", "malawi", "malaysia", "maldives", "mali", "malta", "marshall islands", "mauritania",
    "mauritius", "mexico", "micronesia", "moldova", "monaco", "mongolia", "montenegro", "morocco",
    "mozambique", "myanmar", "namibia", "nauru", "nepal", "netherlands", "new zealand", "nicaragua",
    "niger", "nigeria", "north korea", "north macedonia", "norway", "oman", "pakistan", "palau",
    "palestine", "panama", "papua new guinea", "paraguay", "peru", "philippines", "poland", "portugal",
    "qatar", "romania", "russia", "rwanda", "saint kitts and nevis", "saint lucia",
    "saint vincent and the grenadines", "samoa", "san marino", "sao tome and principe", "saudi arabia",
    "senegal", "serbia", "seychelles", "sierra leone", "singapore", "slovakia", "slovenia",
    "solomon islands", "somalia", "south africa", "south korea", "south sudan", "spain", "sri lanka",
    "sudan", "suriname", "sweden", "switzerland", "syria", "taiwan", "tajikistan", "tanzania", "thailand",
    "timor-leste", "togo", "tonga", "trinidad and tobago", "tunisia", "turkey", "turkmenistan",
    "tuvalu", "uganda", "ukraine", "united arab emirates", "uae", "dubai", "united kingdom", "uk",
    "england", "scotland", "wales", "united states", "united states of america", "usa", "us", "america",
    "uruguay", "uzbekistan", "vanuatu", "vatican city", "venezuela", "vietnam", "yemen", "zambia", "zimbabwe", "global"
}

def validate_country_strict(country):
    if not country or not str(country).strip():
        return True, "Global"

    c_str = str(country).strip()
    c_clean = c_str.lower()

    if re.search(r'\d', c_clean):
        return False, f"⚠️ Invalid Country: '{country}' contains numbers. Please enter a valid country name (e.g. India, USA, Germany, UK, Canada)."

    is_valid = (c_clean in REAL_WORLD_COUNTRIES) or any(valid_c in c_clean for valid_c in REAL_WORLD_COUNTRIES)
    if not is_valid:
        return False, f"⚠️ Invalid Country: '{country}' is not a recognized world country. Please enter a valid country name (e.g. India, USA, Germany, UK, Canada)."

    return True, c_str.title()

    return True, c_str[0].upper() + c_str[1:]

def validate_country(country):
    is_valid, res = validate_country_strict(country)
    if not is_valid:
        return "India"
    return res
def get_total_months(duration):

    duration = duration.lower().strip()

    if duration == "":
        return 6

    month = re.search(r"(\d+)\s*(month|months|m)", duration)

    if month:
        return int(month.group(1))

    year = re.search(r"(\d+)\s*(year|years|y)", duration)

    if year:
        return int(year.group(1)) * 12

    return 6
# =====================================================
# Gemini Error Handler
# =====================================================

def handle_gemini_error(e):
    raw_error = str(e)
    audit_logger.log_event(
        event_type="GEMINI_API_ERROR",
        status="FAILURE",
        details={"error_type": type(e).__name__},
        level=30
    )

    if "RESOURCE_EXHAUSTED" in raw_error or "429" in raw_error:
        return failure(
            "🚫 Gemini API quota exceeded. Please wait 1 minute and try again, or use another API key.",
            429
        )

    if "401" in raw_error or "UNAUTHENTICATED" in raw_error:
        return failure(
            "🔑 Authentication failure with upstream AI service. Please verify server API key configuration.",
            401
        )

    # Scrub potential secrets or API keys
    safe_error = audit_logger.sanitize_message(raw_error)
    if "Traceback" in safe_error or "File \"" in safe_error or "api_key" in safe_error.lower():
        safe_error = "An error occurred during AI processing. Please try again or refine your query."

    return failure(safe_error)

    

# =====================================================
# Startup Diagnostics (Safe / Non-blocking)
# =====================================================

try:
    print("\n===============================")
    print("CareerVerse AI Started with Secure Processing Layer")
    print(f"Security Mode: {get_security_status()['display_badge']}")
    print("===============================")
    if os.getenv("PROBE_MODELS_ON_STARTUP", "false").lower() == "true":
        print("Available Models:\n")
        for model in client.models.list():
            print(model.name)
        print("===============================\n")
except Exception as e:
    print(f"Startup notice: {e}")


# =====================================================
# Home
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# Generate Roadmap Page
# =====================================================

@app.route("/generate")
def generate():
    return render_template("generate.html")


# =====================================================
# About
# =====================================================

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/support")
def support():
    return render_template("support.html")


# =====================================================
# AI Hub
# =====================================================

@app.route("/ai-tools")
def ai_tools():
    return render_template("ai_tools.html")
# =====================================================
# Career Evolution AI
# =====================================================

@app.route("/career-intelligence")
def career_intelligence():
    return render_template("career_intelligence.html")


# =====================================================
# AI Career Assistant
# =====================================================

@app.route("/career-chat")
def career_chat():
    return render_template("career_chat.html")


# =====================================================
# Resume Analyzer
# =====================================================

@app.route("/resume")
def resume():
    return render_template("resume_analyzer.html")


# =====================================================
# Skill Gap Analyzer
# =====================================================

@app.route("/skill-gap")
def skill_gap():
    return render_template("skill_gap.html")
# =====================================================
# Career Reality
# =====================================================

@app.route("/career-reality")
def career_reality_page():
    return render_template("career_reality.html")


# =====================================================
# Career Match
# =====================================================

@app.route("/career-match")
def career_match():
    return render_template("career_match.html")


# =====================================================
# Career Comparison
# =====================================================

@app.route("/compare")
def compare():
    return render_template("career_compare.html")


# =====================================================
# Salary Predictor
# =====================================================

@app.route("/salary-predictor")
def salary_predictor():
    return render_template("salary_predictor.html")


# =====================================================
# Universal Career Validation Endpoint
# =====================================================

@app.route("/validate-career", methods=["POST"])
def validate_career_route():
    try:
        data = request.get_json() or {}
        career_input = data.get("career", "") or data.get("career_input", "")
        res = validate_career_universal(career_input)
        return jsonify(res)
    except Exception as e:
        return jsonify({
            "valid": False,
            "normalized_input": None,
            "input_type": "invalid",
            "error": "Error validating career input."
        }), 500

# =====================================================
# Clear Chat (Per-User Session)
# =====================================================

@app.route("/clear-chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    session.modified = True
    return jsonify({
        "success": True
    })

# =====================================================
# AI Career Chat API (Per-User Isolated Session Memory)
# =====================================================

@app.route("/career-chat-api", methods=["POST"])
def career_chat_api():
    try:
        data = request.get_json() or {}
        question = data.get("question", "").strip()

        if not question:
            return failure("Please enter a question.", 400)

        # Retrieve isolated per-user chat history from Flask session
        history = session.get("chat_history", [])
        if not isinstance(history, list):
            history = []

        history.append({
            "role": "user",
            "text": question
        })

        # Keep last 10 messages for context efficiency
        history = history[-10:]

        prompt = """
You are CareerVerse AI.

You are an intelligent AI Career Mentor.

Remember the previous conversation.

Answer naturally like ChatGPT.

You help with:

• Career Guidance
• Learning Roadmaps
• Resume Review
• Interview Preparation
• Salary Guidance (Ensure numbers are 80-90% accurate to real, current market data)
• Skill Gap Analysis
• Courses
• Books
• Certifications
• Official Documentation
• Government Exams
• Medical Careers
• Engineering Careers
• Business Careers

Always give practical advice.

Conversation:

"""
        for msg in history:
            prompt += f"{msg['role']}: {msg['text']}\n"

        prompt += "\nAssistant:"

        answer = generate_with_fallback(prompt)

        history.append({
            "role": "assistant",
            "text": answer
        })

        # Save updated history back to Flask session
        session["chat_history"] = history
        session.modified = True

        return success({
            "answer": answer
        })

    except Exception as e:
        traceback.print_exc()
        return handle_gemini_error(e)
    
GLOBAL_CURRENCY_DB = {
    # Asia & South Asia
    "india": ("₹", "L / yr", "₹6.5L - ₹10.0L / yr", "₹14.0L - ₹22.0L / yr", "₹25.0L - ₹48.0L / yr"),
    "japan": ("¥", "M / yr", "¥4.5M - ¥6.2M / yr", "¥7.0M - ¥10.5M / yr", "¥12.0M - ¥18.0M / yr"),
    "south korea": ("₩", "M / yr", "₩38M - ₩55M / yr", "₩65M - ₩95M / yr", "₩110M - ₩175M / yr"),
    "korea": ("₩", "M / yr", "₩38M - ₩55M / yr", "₩65M - ₩95M / yr", "₩110M - ₩175M / yr"),
    "china": ("¥", "k / yr", "¥120k - ¥180k / yr", "¥220k - ¥350k / yr", "¥400k - ¥650k / yr"),
    "taiwan": ("NT$", "k / yr", "NT$650k - NT$950k / yr", "NT$1.2M - NT$1.8M / yr", "NT$2.2M - NT$3.5M / yr"),
    "hong kong": ("HK$", "k / yr", "HK$220k - HK$320k / yr", "HK$380k - HK$580k / yr", "HK$680k - HK$1.1M / yr"),
    "singapore": ("S$", "k / yr", "S$48k - S$68k / yr", "S$72k - S$108k / yr", "S$115k - S$180k / yr"),
    "malaysia": ("RM ", "/ mo", "RM 4,500 - RM 7,000 / mo", "RM 8,500 - RM 14,000 / mo", "RM 16,000 - RM 28,000 / mo"),
    "thailand": ("฿", "/ mo", "฿35,000 - ฿55,000 / mo", "฿65,000 - ฿105,000 / mo", "฿120,000 - ฿210,000 / mo"),
    "indonesia": ("Rp ", "/ mo", "Rp 8,000,000 - Rp 14,000,000 / mo", "Rp 16,000,000 - Rp 28,000,000 / mo", "Rp 32,000,000 - Rp 55,000,000 / mo"),
    "vietnam": ("₫", "/ mo", "₫15,000,000 - ₫25,000,000 / mo", "₫30,000,000 - ₫50,000,000 / mo", "₫60,000,000 - ₫110,000,000 / mo"),
    "philippines": ("₱", "/ mo", "₱30,000 - ₱50,000 / mo", "₱60,000 - ₱95,000 / mo", "₱110,000 - ₱180,000 / mo"),
    "pakistan": ("PKR ", "/ mo", "PKR 85,000 - PKR 140,000 / mo", "PKR 160,000 - PKR 280,000 / mo", "PKR 320,000 - PKR 550,000 / mo"),
    "bangladesh": ("BDT ", "/ mo", "BDT 35,000 - BDT 60,000 / mo", "BDT 70,000 - BDT 120,000 / mo", "BDT 140,000 - BDT 250,000 / mo"),
    "sri lanka": ("LKR ", "/ mo", "LKR 75,000 - LKR 125,000 / mo", "LKR 140,000 - LKR 240,000 / mo", "LKR 280,000 - LKR 480,000 / mo"),

    # Americas & Caribbean
    "united states": ("$", "k / yr", "$70k - $95k / yr", "$120k - $160k / yr", "$180k - $270k / yr"),
    "usa": ("$", "k / yr", "$70k - $95k / yr", "$120k - $160k / yr", "$180k - $270k / yr"),
    "canada": ("CA$", "k / yr", "CA$55k - CA$75k / yr", "CA$80k - CA$115k / yr", "CA$125k - CA$185k / yr"),
    "mexico": ("MEX$", "/ mo", "MEX$ 18,000 - MEX$ 32,000 / mo", "MEX$ 38,000 - MEX$ 65,000 / mo", "MEX$ 75,000 - MEX$ 130,000 / mo"),
    "brazil": ("R$", "/ mo", "R$ 5,500 - R$ 9,000 / mo", "R$ 11,000 - R$ 18,000 / mo", "R$ 22,000 - R$ 38,000 / mo"),
    "argentina": ("ARS$", "/ mo", "ARS$ 650,000 - ARS$ 1,100,000 / mo", "ARS$ 1,300,000 - ARS$ 2,200,000 / mo", "ARS$ 2,500,000 - ARS$ 4,500,000 / mo"),
    "chile": ("CLP$", "/ mo", "CLP$ 950,000 - CLP$ 1,600,000 / mo", "CLP$ 1,800,000 - CLP$ 3,000,000 / mo", "CLP$ 3,500,000 - CLP$ 6,000,000 / mo"),

    # Europe & UK
    "united kingdom": ("£", "k / yr", "£32,000 - £48,000 / yr", "£52,000 - £80,000 / yr", "£85,000 - £140,000 / yr"),
    "uk": ("£", "k / yr", "£32,000 - £48,000 / yr", "£52,000 - £80,000 / yr", "£85,000 - £140,000 / yr"),
    "germany": ("€", "k / yr", "€42,000 - €58,000 / yr", "€62,000 - €88,000 / yr", "€95,000 - €150,000 / yr"),
    "france": ("€", "k / yr", "€40,000 - €55,000 / yr", "€58,000 - €82,000 / yr", "€90,000 - €140,000 / yr"),
    "netherlands": ("€", "k / yr", "€45,000 - €62,000 / yr", "€65,000 - €92,000 / yr", "€98,000 - €155,000 / yr"),
    "switzerland": ("CHF ", "k / yr", "CHF 75,000 - CHF 95,000 / yr", "CHF 105,000 - CHF 140,000 / yr", "CHF 150,000 - CHF 220,000 / yr"),

    # Middle East & Africa
    "united arab emirates": ("AED ", "/ mo", "AED 12,000 - AED 18,000 / mo", "AED 22,000 - AED 35,000 / mo", "AED 40,000 - AED 65,000 / mo"),
    "uae": ("AED ", "/ mo", "AED 12,000 - AED 18,000 / mo", "AED 22,000 - AED 35,000 / mo", "AED 40,000 - AED 65,000 / mo"),
    "dubai": ("AED ", "/ mo", "AED 12,000 - AED 18,000 / mo", "AED 22,000 - AED 35,000 / mo", "AED 40,000 - AED 65,000 / mo"),
    "saudi arabia": ("SAR ", "/ mo", "SAR 10,000 - SAR 16,000 / mo", "SAR 18,000 - SAR 28,000 / mo", "SAR 32,000 - SAR 55,000 / mo"),
    "qatar": ("QAR ", "/ mo", "QAR 11,000 - QAR 17,000 / mo", "QAR 20,000 - QAR 32,000 / mo", "QAR 38,000 - QAR 60,000 / mo"),
    "south africa": ("R ", "/ mo", "R 22,000 - R 38,000 / mo", "R 42,000 - R 68,000 / mo", "R 75,000 - R 130,000 / mo"),
    "nigeria": ("₦", "/ mo", "₦ 350,000 - ₦ 600,000 / mo", "₦ 700,000 - ₦ 1,200,000 / mo", "₦ 1,500,000 - ₦ 2,800,000 / mo"),
    "kenya": ("KSh ", "/ mo", "KSh 85,000 - KSh 140,000 / mo", "KSh 160,000 - KSh 260,000 / mo", "KSh 300,000 - KSh 520,000 / mo"),

    # Oceania
    "australia": ("A$", "k / yr", "A$65,000 - A$88,000 / yr", "A$92,000 - A$130,000 / yr", "A$140,000 - A$210,000 / yr"),
    "new zealand": ("NZ$", "k / yr", "NZ$60,000 - NZ$82,000 / yr", "NZ$85,000 - NZ$120,000 / yr", "NZ$130,000 - NZ$190,000 / yr")
}

def get_country_salary_tuple(country, default_f="$70,000 - $95,000 / yr", default_m="$120,000 - $160,000 / yr", default_s="$180,000 - $270,000 / yr"):
    c_low = (country or "").lower().strip()
    for key, (symbol, unit, f_val, m_val, s_val) in GLOBAL_CURRENCY_DB.items():
        if key in c_low:
            return f_val, m_val, s_val
    return default_f, default_m, default_s

def format_multi_currency_salary(country, base_usd_fresher="$70k - $95k / yr", base_usd_mid="$120k - $160k / yr", base_usd_senior="$180k - $270k / yr"):
    c_low = (country or "").lower().strip()
    
    for key, (symbol, unit, f_val, m_val, s_val) in GLOBAL_CURRENCY_DB.items():
        if key in c_low:
            return f"{f_val} (Fresher) -> {m_val} (Mid) -> {s_val} (Senior)"

    c_name = country.title() if country else "Target Country"
    return f"{c_name}: {base_usd_fresher} (Fresher) -> {base_usd_mid} (Mid) -> {base_usd_senior} (Senior)"

# =====================================================
# Career-Specific Salary Benchmarking Engine
# =====================================================

# =====================================================
# Universal Country Currency Benchmarking Engine
# =====================================================

def get_country_currency_info(country):
    c_clean = (country or "Global").strip()

    # Direct case-insensitive search in COUNTRY_CURRENCY json
    for k, v in COUNTRY_CURRENCY.items():
        if k.lower() == c_clean.lower():
            parts = v.split()
            code = parts[0] if len(parts) > 0 else "USD"
            symbol = parts[1] if len(parts) > 1 else "$"
            return k, code, symbol

    # Substring search
    for k, v in COUNTRY_CURRENCY.items():
        if k.lower() in c_clean.lower() or c_clean.lower() in k.lower():
            parts = v.split()
            code = parts[0] if len(parts) > 0 else "USD"
            symbol = parts[1] if len(parts) > 1 else "$"
            return k, code, symbol

    # Specific country name overrides
    c_low = c_clean.lower()
    if "india" in c_low:
        return "India", "INR", "₹"
    elif "china" in c_low:
        return "China", "CNY", "¥"
    elif "japan" in c_low:
        return "Japan", "JPY", "¥"
    elif "uk" in c_low or "united kingdom" in c_low or "england" in c_low:
        return "United Kingdom", "GBP", "£"
    elif "germany" in c_low or "france" in c_low or "europe" in c_low or "eu" in c_low:
        return c_clean.title(), "EUR", "€"
    elif "usa" in c_low or "united states" in c_low or "america" in c_low:
        return "United States", "USD", "$"

    return c_clean.title(), "USD", "$"


def get_career_salary_benchmark(career, country):
    from salary_data_layer import get_verified_salary_data, normalize_country_key, COUNTRY_CURRENCY_REGISTRY, get_category_salary_benchmark
    import json
    
    c_norm = normalize_country_key(country)
    
    # Step 1: Check verified hardcoded database first
    res = get_verified_salary_data(career, country)
    if res.get("salary") and (res["salary"].get("min") or res["salary"].get("fresher")):
        v_sal = res["salary"]
        fresher_val = v_sal.get("fresher") or v_sal.get("min")
        mid_val = v_sal.get("mid") or v_sal.get("median")
        senior_val = v_sal.get("senior") or v_sal.get("max")
        return {
            "fresher": fresher_val,
            "mid": mid_val,
            "senior": senior_val,
            "reason": f"Verified market compensation rates pulled from {res.get('sources_checked', ['official labour records'])[0] if res.get('sources_checked') else 'government labor agencies'}."
        }

    # Step 2: Use LLM dynamic query for high-fidelity active market rates in 2026
    c_name, code, symbol = get_country_currency_info(country)
    prompt = f"""
You are a global compensation benchmarking AI.
Analyze the current 2026 market compensation rates for:
Role: "{career}"
Country: "{c_name}"

You must return ONLY a valid JSON object matching this structure (no markdown fences, no other text):
{{
  "fresher": "<fresher_annual_salary_range_formatted_with_currency_symbol>",
  "mid": "<mid_annual_salary_range_formatted_with_currency_symbol>",
  "senior": "<senior_annual_salary_range_formatted_with_currency_symbol>",
  "reason": "<detailed_one_sentence_explanation_of_why_this_role_commands_this_salary_based_on_local_market_forces>"
}}

Rules:
1. Use the local currency of {c_name} ({code}, Symbol: {symbol}). Do NOT output Indian Rupees (INR/₹) unless {c_name} is India.
2. Ensure the ranges are highly realistic and align with active 2026 market signals.
"""
    try:
        raw_text = generate_with_fallback(prompt)
        cleaned_text = clean_json(raw_text)
        data = json.loads(cleaned_text)
        if data.get("fresher") and data.get("mid") and data.get("senior"):
            return {
                "fresher": data["fresher"].strip(),
                "mid": data["mid"].strip(),
                "senior": data["senior"].strip(),
                "reason": data.get("reason", "").strip()
            }
    except Exception as e:
        print(f"Failed to resolve real-time salary benchmarks for '{career}' in '{country}': {e}")

    # Step 3: Global average category fallback (static backup)
    curr_meta = COUNTRY_CURRENCY_REGISTRY.get(c_norm, {"code": "USD", "symbol": "$", "name": "United States dollar"})
    bm = get_category_salary_benchmark(career, c_norm, curr_meta)
    return {
        "fresher": bm["fresher_fmt"],
        "mid": bm["mid_fmt"],
        "senior": bm["senior_fmt"],
        "reason": f"Estimated baseline average for {c_norm.title()} market based on national service scales."
    }




INDIAN_EXAM_REGEX = re.compile(
    r'(\b(upsc|ias|ips|ifs|irs|ies|ssc|gate|nda|cds|afcat|inet|mpsc|bpsc|uppsc|ras|gpsc|kpsc|opsc|ppsc|hpsc|cgpsc|tnpsc|tspsc|appsc|wbcs|jkpsc|mppsc|jee|neet|cat|clat|nift|nid|ibps|sbi|rbi|nabard|epfo|rrb|isro|drdo|barc|hal|bel|gail|ntpc|cgl|chsl|mts|cpo|mhcer|mhcet|kcet|keam|eamcet|wbjee|ojee|gujcet|upcee|assammed|jkcet|hp-cet|upcemet|mp-pat|bihar-cet|uksee)\b)|(.*cet$)|(.*psc$)|(.*eamcet$)',
    re.IGNORECASE
)

def is_indian_exam(career_text):
    if not career_text:
        return False
    c_clean = str(career_text).lower().strip()
    if INDIAN_EXAM_REGEX.search(c_clean):
        return True
    words = c_clean.split()
    for w in words:
        if w.endswith("cet") or w.endswith("psc") or w.endswith("eamcet") or w.endswith("jee"):
            return True
    return False

def create_normalized_salary_object(career, country):
    from salary_data_layer import enforce_currency_symbol
    country_clean = country.title() if country else "India"
    
    if is_indian_exam(career) and country_clean.lower() not in ["india", "in", "bharat"]:
        c_name = f"India (Native {career.upper()} Structure)"
        code = "INR"
        symbol = "₹"
        bench = get_career_salary_benchmark(career, "India")
    else:
        c_name, code, symbol = get_country_currency_info(country)
        bench = get_career_salary_benchmark(career, country)

    fresher_clean = enforce_currency_symbol(bench["fresher"], symbol)
    mid_clean = enforce_currency_symbol(bench["mid"], symbol)
    senior_clean = enforce_currency_symbol(bench["senior"], symbol)

    target_formatted = f"{fresher_clean} (Fresher) -> {mid_clean} (Mid) -> {senior_clean} (Senior)"
    
    reason = bench.get("reason") or f"Compensation levels for a {career} in {c_name} are driven by high cognitive demand, specialized technical expertise, and local talent scarcity."

    return {
        "target_location": c_name,
        "country": c_name,
        "currency_symbol": symbol,
        "currency_code": code,
        "fresher": fresher_clean,
        "mid": mid_clean,
        "senior": senior_clean,
        "country_fresher": fresher_clean,
        "country_mid": mid_clean,
        "country_senior": senior_clean,
        "india_fresher": fresher_clean,
        "india_mid": mid_clean,
        "india_senior": senior_clean,
        "formatted_range": target_formatted,
        "reason": reason
    }

HOTSPOTS_DATABASE = {
    "india": [
        {"city": "Bengaluru", "demand": "Very High", "reason": "Silicon Valley of India, tech unicorns & R&D hubs."},
        {"city": "Mumbai", "demand": "Very High", "reason": "Financial capital, entertainment & corporate HQs."},
        {"city": "Hyderabad", "demand": "High", "reason": "Major IT, pharmaceutical & global GCC hubs."},
        {"city": "Pune", "demand": "High", "reason": "Automotive R&D, IT services & engineering hubs."},
        {"city": "Delhi NCR", "demand": "High", "reason": "National capital region, e-commerce & corporate HQs."}
    ],
    "united kingdom": [
        {"city": "London", "demand": "Very High", "reason": "UK capital, major studio HQs & international corporate hubs."},
        {"city": "Manchester", "demand": "High", "reason": "Leading UK digital media, tech & innovation center."},
        {"city": "Birmingham", "demand": "High", "reason": "Major commercial & industrial hub with growing hiring demand."},
        {"city": "Bristol", "demand": "High", "reason": "Premier creative tech, animation & engineering ecosystem."},
        {"city": "Edinburgh", "demand": "Moderate-High", "reason": "Financial services, tech startups & academic research hub."}
    ],
    "united states": [
        {"city": "San Francisco", "demand": "Very High", "reason": "Global tech epicenter, venture capital and startup hub."},
        {"city": "New York", "demand": "Very High", "reason": "Financial capital, media conglomerate HQs and startup ecosystem."},
        {"city": "Austin", "demand": "High", "reason": "Major tech hub, favorable tax environment and hardware engineering hub."},
        {"city": "Seattle", "demand": "High", "reason": "Cloud infrastructure giants (Amazon, Microsoft) and enterprise software."},
        {"city": "Boston", "demand": "High", "reason": "Leading hub for biotechnology, robotics and higher education research."}
    ],
    "canada": [
        {"city": "Toronto", "demand": "Very High", "reason": "Financial core of Canada, massive tech and AI research hubs."},
        {"city": "Vancouver", "demand": "Very High", "reason": "Major hub for VFX, game development, and tech startups."},
        {"city": "Montreal", "demand": "High", "reason": "Global gaming studio cluster and AI research center."},
        {"city": "Ottawa", "demand": "High", "reason": "Public sector tech, telecommunications and SaaS companies."},
        {"city": "Calgary", "demand": "Moderate-High", "reason": "Energy sector tech, logistics and growing software hubs."}
    ],
    "australia": [
        {"city": "Sydney", "demand": "Very High", "reason": "Financial heart, tech HQs and dominant startup ecosystem."},
        {"city": "Melbourne", "demand": "Very High", "reason": "Creative tech, design, biotech and major cultural tech hub."},
        {"city": "Brisbane", "demand": "High", "reason": "Growing software development, aviation and resource tech center."},
        {"city": "Adelaide", "demand": "Moderate-High", "reason": "Defense tech, space industry and engineering hub."},
        {"city": "Perth", "demand": "Moderate-High", "reason": "Resource tech, mining software and maritime engineering."}
    ],
    "germany": [
        {"city": "Berlin", "demand": "Very High", "reason": "Startup capital of Europe, creative tech and fintech hubs."},
        {"city": "Munich", "demand": "Very High", "reason": "Automotive tech, engineering and corporate Siemens/BMW HQs."},
        {"city": "Frankfurt", "demand": "High", "reason": "Financial capital of Eurozone, banking tech and cloud centers."},
        {"city": "Hamburg", "demand": "High", "reason": "Logistics, media, game development and commerce hubs."},
        {"city": "Stuttgart", "demand": "Moderate-High", "reason": "Industrial manufacturing, mechanical engineering and automotive."}
    ],
    "france": [
        {"city": "Paris", "demand": "Very High", "reason": "Capital city, startup incubators and corporate headquarters."},
        {"city": "Lyon", "demand": "High", "reason": "Biotech, chemical engineering and digital entertainment hub."},
        {"city": "Toulouse", "demand": "High", "reason": "European aerospace capital, aviation engineering and robotics."},
        {"city": "Nantes", "demand": "Moderate-High", "reason": "Creative tech, green energy startups and digital agencies."},
        {"city": "Sophia Antipolis", "demand": "High", "reason": "Major technology park for telecom, AI and microelectronics."}
    ]
}

def sanitize_market_hiring_data(market_dict, country, career):
    if not isinstance(market_dict, dict):
        return market_dict
    c_low = (country or "").lower().strip()
    
    from salary_data_layer import normalize_country_key
    c_norm = normalize_country_key(c_low)
    
    target_key = None
    for k in HOTSPOTS_DATABASE.keys():
        if k in c_norm or c_norm in k:
            target_key = k
            break
            
    hotspots = market_dict.get("hiring_hotspots", [])
    if not isinstance(hotspots, list):
        hotspots = []
        
    if target_key == "united kingdom":
        if any("san francisco" in str(h).lower() or "austin" in str(h).lower() or "new york" in str(h).lower() for h in hotspots):
            hotspots = []
    elif target_key == "india":
        if any("san francisco" in str(h).lower() or "austin" in str(h).lower() for h in hotspots):
            hotspots = []
            
    if len(hotspots) < 5:
        if target_key and target_key in HOTSPOTS_DATABASE:
            default_list = HOTSPOTS_DATABASE[target_key]
            existing_names = {h.get("city", "").lower() for h in hotspots if isinstance(h, dict) and h.get("city")}
            for default_item in default_list:
                if len(hotspots) >= 5:
                    break
                if default_item["city"].lower() not in existing_names:
                    hotspots.append(default_item)
        else:
            c_title = country.title()
            default_fallbacks = [
                {"city": f"Capital District, {c_title}", "demand": "Very High", "reason": f"Administrative center, commercial hub and major hiring node in {c_title}."},
                {"city": f"Metropolitan Center, {c_title}", "demand": "High", "reason": f"Principal financial district, corporate HQs and service sector in {c_title}."},
                {"city": f"Technology Park, {c_title}", "demand": "High", "reason": f"Special economic zone, innovation parks and regional development in {c_title}."},
                {"city": f"Industrial Zone, {c_title}", "demand": "Moderate-High", "reason": f"Manufacturing powerhouse, logistics infrastructure and production in {c_title}."},
                {"city": f"Coastal Port City, {c_title}", "demand": "Moderate-High", "reason": f"Trade gateway, import-export commerce and shipping hub in {c_title}."}
            ]
            existing_names = {h.get("city", "").lower() for h in hotspots if isinstance(h, dict) and h.get("city")}
            for default_item in default_fallbacks:
                if len(hotspots) >= 5:
                    break
                if default_item["city"].lower() not in existing_names:
                    hotspots.append(default_item)
                    
    sanitized_hotspots = []
    for h in hotspots[:5]:
        if isinstance(h, dict):
            city_name = h.get("city") or h.get("name") or "Key Commercial Hub"
            demand_val = h.get("demand") or h.get("demand_level") or "High"
            reason_val = h.get("reason") or h.get("justification") or f"Growing recruitment activity for {career} specialists."
            sanitized_hotspots.append({
                "city": city_name,
                "demand": demand_val,
                "reason": reason_val
            })
        else:
            sanitized_hotspots.append({
                "city": str(h),
                "demand": "High",
                "reason": f"Active talent recruitment and hiring demand for {career} roles."
            })
            
    while len(sanitized_hotspots) < 5:
        idx = len(sanitized_hotspots) + 1
        sanitized_hotspots.append({
            "city": f"Regional Hub #{idx}",
            "demand": "High",
            "reason": f"Expanding industry presence and hiring demand for {career} specialists."
        })
        
    market_dict["hiring_hotspots"] = sanitized_hotspots

    # Sanitize organizations
    orgs = market_dict.get("top_organizations", [])
    if not isinstance(orgs, list):
        orgs = []
    if target_key == "united kingdom":
        has_indian_conglom = any("tata" in str(o).lower() or "reliance" in str(o).lower() for o in orgs)
        if (has_indian_conglom or not orgs) and any(w in (career or "").lower() for w in ["3d", "artist", "animat", "vfx", "game", "design"]):
            market_dict["top_organizations"] = ["DNEG (London)", "Framestore", "Industrial Light & Magic (London)", "Creative Assembly", "Sony PlayStation Studios UK"]
            
    return market_dict

# =====================================================
# Fallback Roadmap Generator
# =====================================================

def get_fallback_roadmap(career, country, months=6):
    c_title = career.strip().title() if career else "Professional"
    c_low = career.lower() if career else ""
    is_india = "india" in (country or "").lower() or not (country or "").strip()
    # Default Initializations to prevent UnboundLocalError
    edu = f"Bachelor's Degree in relevant field or equivalent professional portfolio for {c_title}"
    sal_ind_f, sal_ind_m, sal_ind_s = "₹4.5L - ₹7.5L / yr", "₹10.0L - ₹18.0L / yr", "₹22.0L - ₹45.0L / yr"
    sal_cnt_f, sal_cnt_m, sal_cnt_s = "$55,000 - $80,000 / yr", "$90,000 - $140,000 / yr", "$160,000 - $260,000 / yr"
    roles = [f"Junior {c_title}", f"Associate {c_title}", f"Senior {c_title}", f"Lead {c_title} Specialist", f"Director / Head of {c_title}"]
    sk_b = [f"Foundational {c_title} Concepts", "Industry Fundamentals", "Basic Tooling & Workflow", "Time Management", "Professional Communication"]
    sk_i = [f"Intermediate {c_title} Execution", "Data Analysis & Metrics", "Problem Solving & Troubleshooting", "Standard Compliance & Safety", "Team Collaboration"]
    sk_a = [f"Advanced {c_title} Strategy", "Leadership & Mentorship", "System Optimization & Scalability", "Risk Management & Planning", "Budgeting & Financial Stewardship"]
    yt = [{"name": "Google Learning Portal", "url": "https://www.youtube.com"}, {"name": "Industry Overview Guides", "url": "https://www.youtube.com"}]
    courses = [{"name": "Coursera Professional Learning", "url": "https://www.coursera.org"}, {"name": "edX Skill Academy", "url": "https://www.edx.org"}]
    docs = [{"name": "Official Industry Guidelines", "url": "https://en.wikipedia.org"}]
    books = [{"name": "Standard Reference Handbook", "url": "https://amazon.com"}]
    projs_b = [f"Basic {c_title} Practical Study", f"Foundational {c_title} Case Study", f"Initial {c_title} Project", "Process Auditing Task", "Standard Report Writing"]
    projs_i = [f"Intermediate {c_title} Portfolio Project", f"Standard {c_title} Quality Audit", f"Client-Facing {c_title} Execution", "Workflow Integration Project", "Team Performance Assessment"]
    projs_a = [f"Advanced {c_title} Strategy Capstone", f"Enterprise {c_title} Deployment Plan", f"Global {c_title} Performance Analysis", "Strategic Resource Allocation Study", "Industry Compliance Review"]
    certs = [f"Certified {c_title} Professional", f"Advanced {c_title} Specialist License", "Standard Project Management Certificate", "Industry Operations Credential", "Professional Development Diploma"]
    tools = ["Standard Enterprise Tools", "Industry Software Utilities", "Process Flow Simulators", "Reporting Dashboards", "Team Collaboration Suite"]
    top_orgs = ["Global Enterprise Systems", "Leading Industry Operations", "National Sector Corporations", "Regional Services Group", "Specialist Consulting Firm"]
    hotspots = [{"city": "Mumbai / India", "demand": "High", "reason": "Major Industrial & Commerce Hub"}, {"city": "New York / USA", "demand": "High", "reason": "Global Corporate Headquarters Hub"}, {"city": "London / UK", "demand": "High", "reason": "International Services Hub"}, {"city": "Bengaluru", "demand": "High", "reason": "Tech & Services Operations Hub"}, {"city": "Delhi NCR", "demand": "Moderate-High", "reason": "Corporate Offices & Government Agencies"}]
    trend_skills = [f"Digital {c_title} Workflows", "Process Automation", "Data-Driven Reporting", "AI-Assisted Efficiency", "Remote Collaboration"]
    daily_plan = ["Monday: 2 hrs Core Principles", "Tuesday: 2 hrs Technical Study", "Wednesday: 2 hrs Tooling Practice", "Thursday: 2 hrs Portfolio Work", "Friday: 2 hrs Weekly Review", "Saturday: 3 hrs Case Study Analysis", "Sunday: 1 hr Weekly Knowledge Assessment"]

    # Sector Classification
    if any(w in c_low for w in ["doctor", "surgeon", "physician", "dentist", "nurse", "medical", "pharmacist"]):
        edu = "MBBS / MD / BDS / Nursing Degree + Clinical Internship & Medical Council Registration"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.0L - ₹10.0L / yr", "₹15.0L - ₹28.0L / yr", "₹35.0L - ₹75.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$75k - $110k / yr", "$150k - $240k / yr", "$280k - $450k / yr"
        roles = [f"Resident {c_title}", f"Junior Consultant {c_title}", f"Senior Consultant {c_title}", f"Head of Clinical Department", f"Medical Director"]
        sk_b = ["Human Anatomy & Physiology", "Medical Terminology", "Vital Signs & Triage", "First Aid & CPR", "Patient Empathy"]
        sk_i = ["Clinical Pharmacology", "Pathology & Diagnostics", "EMR/EHR Systems (Epic/Cerner)", "Emergency Resuscitation", "Surgical Hygiene"]
        sk_a = ["Advanced Surgical Protocols", "Critical ICU Management", "Complex Differential Diagnosis", "Clinical Research & Publishing", "Hospital Governance"]
        yt = [{"name": "Osmosis by Elseveir", "url": "https://www.youtube.com/@osmosis"}, {"name": "Ninja Nerd - Medicine", "url": "https://www.youtube.com/@NinjaNerdOfficial"}, {"name": "Doctor Mike", "url": "https://www.youtube.com/@DoctorMike"}, {"name": "Armando Hasudungan", "url": "https://www.youtube.com/@armandohasudungan"}, {"name": "Khan Academy Medicine", "url": "https://www.youtube.com/@khanacademy"}]
        courses = [{"name": "Harvard Medical School Online", "url": "https://online-learning.harvard.edu"}, {"name": "Coursera Clinical Medicine", "url": "https://www.coursera.org"}, {"name": "Stanford Health & Medicine", "url": "https://online.stanford.edu"}, {"name": "edX Anatomy & Physiology", "url": "https://www.edx.org"}, {"name": "Lecturio Medical Education", "url": "https://www.lecturio.com"}]
        docs = [{"name": "WHO Clinical Guidelines", "url": "https://www.who.int"}, {"name": "PubMed Central Literature", "url": "https://pmc.ncbi.nlm.nih.gov"}, {"name": "UpToDate Clinical Decision Support", "url": "https://www.uptodate.com"}, {"name": "CDC Health Protocols", "url": "https://www.cdc.gov"}, {"name": "ICMR Guidelines", "url": "https://www.icmr.gov.in"}]
        books = [{"name": "Harrison's Principles of Internal Medicine", "url": "https://amazon.com"}, {"name": "Gray's Anatomy for Students", "url": "https://amazon.com"}, {"name": "Robbins & Cotran Pathologic Basis of Disease", "url": "https://amazon.com"}, {"name": "Katzung Basic & Clinical Pharmacology", "url": "https://amazon.com"}, {"name": "Oxford Handbook of Clinical Medicine", "url": "https://amazon.com"}]
        projs_b = ["Patient Case Logbook Analysis", "Vital Signs Monitoring Study", "Pharmacology Dosage Calculation Chart", "First Aid Emergency Plan", "Basic Clinical Hygiene Audit"]
        projs_i = ["Diagnostic Case Study Portfolio", "EHR Clinical Workflow Design", "Hospital Ward Infection Control Audit", "Pharmacovigilance Adverse Event Study", "Emergency ICU Triage Simulation"]
        projs_a = ["Clinical Research Trial Design", "Complex Surgical Case Study Publication", "Hospital Departmental EMR System Upgrade", "Public Health Epidemic Response Protocol", "Medical Ethics Case Review"]
        certs = ["ACLS & BLS Certification", "Medical Board Registration / USMLE", "NEET PG / PLAB Specialist License", "Certified Electronic Health Record Specialist", "Critical Care Medicine Diploma"]
        tools = ["Diagnostic Stethoscope & Otoscope", "Epic / Cerner EMR Systems", "Medical Pulse Oximeter & ECG", "Surgical Instrument Set", "UpToDate Clinical Database"]
        top_orgs = ["Mayo Clinic", "AIIMS New Delhi", "Johns Hopkins Hospital", "NHS UK", "Apollo Hospitals"]
        hotspots = [{"city": "Delhi NCR", "demand": "Very High", "reason": "National premier medical institutes & super-specialty hospitals."}, {"city": "Boston / USA", "demand": "High", "reason": "Global hub for clinical research & Harvard teaching hospitals."}, {"city": "Mumbai", "demand": "High", "reason": "Leading private hospital networks & medical research hubs."}, {"city": "London / UK", "demand": "High", "reason": "NHS tertiary referral centers & medical universities."}, {"city": "Bengaluru", "demand": "Moderate-High", "reason": "Growing health-tech & multi-specialty hospital infrastructure."}]
        trend_skills = ["Robotic Surgery Protocols", "Digital EMR Data Analysis", "Telemedicine Consultation", "Precision Diagnostics", "Genomic Medicine"]
        daily_plan = ["Monday: 2 hrs Anatomy & Pathophysiology Deep Dive", "Tuesday: 2 hrs Clinical Case Study Analysis", "Wednesday: 2 hrs Pharmacology & Drug Interaction Review", "Thursday: 2 hrs EMR Documentation & Patient Simulation", "Friday: 2 hrs Clinical Rotations & Case Reviews", "Saturday: 3 hrs Diagnostic Rounds & Journal Review", "Sunday: 1 hr Weekly Medical Knowledge Assessment"]
    elif any(w in c_low for w in ["brihanmumbai", "bmc", "mcgm", "municipal", "civic"]):
        edu = "Degree / Diploma in Civil, Mechanical, Electrical Engineering or Public Administration + BMC / MPSC Selection Exam"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.0L - ₹9.5L / yr", "₹12.0L - ₹18.0L / yr", "₹22.0L - ₹38.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$60k - $85k / yr", "$95k - $130k / yr", "$150k - $210k / yr"
        roles = ["BMC Sub-Engineer / Junior Engineer", "BMC Assistant Engineer (AE)", "BMC Executive Engineer (EE)", "BMC Deputy Municipal Commissioner (DMC)", "BMC Additional Municipal Commissioner / Municipal Commissioner"]
        sk_b = ["Mumbai Municipal Corporation Act (MMC Act 1888)", "Development Control & Promotion Regulations (DCPR 2034)", "Civil Engineering & Urban Infrastructure", "BMC e-Tendering & Public Procurement", "Public Health & Solid Waste Management (SWM)"]
        sk_i = ["BMC Water Supply Engineering (Bhandup Complex / Vaitarna)", "Disaster Management & Monsoon Flood Control (1916 Control Room)", "Building Proposal Department (BP Dept) Approvals", "AutoCAD & GIS Urban Mapping", "Sewerage Operations & Environmental Engineering"]
        sk_a = ["Civic Megaproject Execution (Coastal Road / Trans-Harbour Link)", "Municipal Budgeting & Revenue Audit", "Inter-Departmental Municipal Governance", "Urban Resilience & Climate Adaptation", "Cabinet & Standing Committee Governance"]
        yt = [{"name": "StudyIQ Civil Services & MPSC", "url": "https://www.youtube.com/@StudyIQEducation"}, {"name": "Infinity Engineering Academy", "url": "https://www.youtube.com/@InfinityEngineeringAcademy"}, {"name": "Ignite Academy Maharashtra", "url": "https://www.youtube.com/@IgniteAcademy"}, {"name": "Testbook MPSC & Civil Exams", "url": "https://www.youtube.com/@TestbookMPSC"}, {"name": "Sansad TV Urban Governance", "url": "https://www.youtube.com/@SansadTV"}]
        courses = [{"name": "Swayam Urban Governance & Municipal Infrastructure", "url": "https://swayam.gov.in"}, {"name": "NPTEL Urban Planning & Civil Engineering", "url": "https://nptel.ac.in"}, {"name": "Coursera Smart Cities & Urban Policy", "url": "https://www.coursera.org"}, {"name": "YASHADA Maharashtra Public Administration", "url": "https://yashada.org"}, {"name": "edX Sustainable Urban Infrastructure", "url": "https://www.edx.org"}]
        docs = [{"name": "BMC (MCGM) Official Portal", "url": "https://www.mcgm.gov.in"}, {"name": "Mumbai Municipal Corporation Act 1888", "url": "https://legislative.gov.in"}, {"name": "DCPR 2034 Development Control Regulations", "url": "https://portal.mcgm.gov.in"}, {"name": "Maharashtra Urban Development Department", "url": "https://urban.maharashtra.gov.in"}, {"name": "National Urban Infrastructure Guidelines", "url": "https://mohua.gov.in"}]
        books = [{"name": "Mumbai Municipal Corporation Act, 1888 Handbook", "url": "https://amazon.com"}, {"name": "Urban Planning and Infrastructure in India by Kulwant Singh", "url": "https://amazon.com"}, {"name": "Civil Engineering Objective Book by R.S. Khurmi", "url": "https://amazon.com"}, {"name": "Development Control Regulations (DCPR 2034) Manual", "url": "https://amazon.com"}, {"name": "Public Administration in India by A. Avasthi", "url": "https://amazon.com"}]
        projs_b = ["BMC Ward Level Public Grievance Audit", "DCPR 2034 Floor Space Index (FSI) Calculation", "Basic Drainage & Pothole Repair Audit", "BMC e-Tender Document Review", "Solid Waste Segregation Plan"]
        projs_i = ["BMC Pumping Station & Stormwater Drainage Audit", "Building Proposal Approval Checklist & Plan Audit", "Bhandup Water Treatment Plant Flow Analysis", "Disaster Management Monsoon Preparedness Plan", "Road Concreting Quality Control Audit"]
        projs_a = ["Mumbai Coastal Road Infrastructure Resilience Review", "State-Level Municipal Solid Waste Management Masterplan", "BMC e-Governance & Single Window Property Tax System", "Suburban Sewerage Network Upgrade Blueprint", "Municipal Standing Committee Budget Proposal"]
        certs = ["BMC Junior Engineer / Assistant Engineer Recruitment Cert", "MPSC Civil Engineering Services Qualification", "Certified AutoDesk AutoCAD / Revit Professional", "Certified GIS Urban Planner", "National Institute of Urban Affairs Cert"]
        tools = ["AutoCAD & Civil 3D", "GIS Geo-Spatial Mapping", "BMC AutoDCR / e-Step Online Plan Approval", "SAP Municipal Resource Planning", "e-Procurement Portal (Mahatenders / BMC)"]
        top_orgs = ["Brihanmumbai Municipal Corporation (BMC)", "MMRDA (Mumbai Metropolitan Region Dev Authority)", "CIDCO Maharashtra", "MHADA", "Maharashtra Water Resources Department"]
        hotspots = [{"city": "Mumbai (BMC Headquarters / Fort)", "demand": "Very High", "reason": "Central Municipal Head Office, Standing Committee & Departmental HQs."}, {"city": "Suburban Mumbai Wards (Andheri/Borivali/Kurla)", "demand": "Very High", "reason": "Major Ward Offices, Building Proposal & Infrastructure Operations."}, {"city": "Navi Mumbai & Thane", "demand": "High", "reason": "Neighboring Municipal Corporations (NMMC/TMC) & Infrastructure."}, {"city": "Pune Municipal Corporation (PMC)", "demand": "High", "reason": "Major Urban Civic Body & Smart City Infrastructure Projects."}, {"city": "Nagpur & Nashik", "demand": "High", "reason": "Key Municipal Infrastructure & Urban Governance Centers."}]
        trend_skills = ["AutoDCR Digital Plan Approvals", "GIS Geo-Spatial Urban Planning", "Monsoon Flood Telemetry & Sensors", "E-Tendering & Public Procurement", "Climate Resilience & Urban Green Tech"]
        daily_plan = ["Monday: 2 hrs MMC Act 1888 & Municipal Regulations", "Tuesday: 2 hrs Civil / Mechanical Technical Subjects Study", "Wednesday: 2 hrs DCPR 2034 Development Control Rules & FSI", "Thursday: 2 hrs BMC e-Tender & AutoDCR Case Studies", "Friday: 2 hrs Previous Year BMC JE / AE Exam Questions", "Saturday: 3 hrs Mock Test & General Knowledge Revision", "Sunday: 1 hr Weekly Progress & Civic Law Review"]
    elif any(w in c_low for w in ["ias", "ips", "upsc", "police", "army", "navy", "air force", "nda", "civil servant", "government"]):
        edu = "Bachelor's Degree in any discipline + UPSC / State Public Service / SSB Selection Board Qualification"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹7.0L - ₹11.0L / yr", "₹14.0L - ₹22.0L / yr", "₹25.0L - ₹40.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$65k - $95k / yr", "$100k - $140k / yr", "$160k - $220k / yr"
        roles = [f"Assistant Magistrate / Probationary Officer", f"Sub-Divisional Magistrate / SP", f"District Collector / DIG", f"Joint Secretary / Inspector General", f"Chief Secretary / Director General of Police"]
        sk_b = ["Indian Polity & Constitution", "Indian History & Culture", "Geography & Environment", "Basic General Mental Ability", "Ethics & Integrity"]
        sk_i = ["Public Administration & Governance", "Economic & Social Development", "Internal Security & Disaster Management", "District Legal Frameworks", "Policy Drafting"]
        sk_a = ["International Relations & Strategy", "Cabinet-Level Policy Formulation", "Crisis Management & Law Enforcement", "Inter-Departmental Coordination", "Public Audit & Budgeting"]
        yt = [{"name": "StudyIQ IAS", "url": "https://www.youtube.com/@StudyIQEducation"}, {"name": "Unacademy UPSC", "url": "https://www.youtube.com/@UnacademyUPSC"}, {"name": "Vision IAS", "url": "https://www.youtube.com/@VisionIASdelhi"}, {"name": "Drishti IAS", "url": "https://www.youtube.com/@DrishtiIASvideos"}, {"name": "Sansad TV Official", "url": "https://www.youtube.com/@SansadTV"}]
        courses = [{"name": "Swayam Public Administration", "url": "https://swayam.gov.in"}, {"name": "NPTEL Governance & Policy", "url": "https://nptel.ac.in"}, {"name": "Coursera Global Public Policy", "url": "https://www.coursera.org"}, {"name": "IGNOU Public Governance", "url": "http://www.ignou.ac.in"}, {"name": "EdX International Relations", "url": "https://www.edx.org"}]
        docs = [{"name": "Constitution of India Portal", "url": "https://legislative.gov.in"}, {"name": "PIB (Press Information Bureau)", "url": "https://pib.gov.in"}, {"name": "NITI Aayog Official Reports", "url": "https://www.niti.gov.in"}, {"name": "Economic Survey of India", "url": "https://www.indiabudget.gov.in"}, {"name": "State Gazette Portal", "url": "https://egazette.gov.in"}]
        books = [{"name": "Indian Polity by M. Laxmikanth", "url": "https://amazon.com"}, {"name": "India's Struggle for Independence by Bipan Chandra", "url": "https://amazon.com"}, {"name": "Certificate Physical Geography by GC Leong", "url": "https://amazon.com"}, {"name": "Ethics, Integrity and Aptitude by Subba Rao", "url": "https://amazon.com"}, {"name": "Indian Economy by Ramesh Singh", "url": "https://amazon.com"}]
        projs_b = ["District Socio-Economic Profile Study", "Constitutional Rights Summary Report", "Local Sanitation Policy Review", "Basic Disaster Response Plan", "Public Grievance Redressal Audit"]
        projs_i = ["Urban Smart City Infrastructure Policy", "Rural Employment Scheme Implementation Audit", "District Crime Trend Analysis & Mitigation", "Environmental Impact Assessment", "Public Distribution System Optimization"]
        projs_a = ["State-Level Disaster Resilience Framework", "National E-Governance Policy Architecture", "Border Security & Inter-Agency Coordination Plan", "Fiscal Policy Reform Memorandum", "Cabinet Briefing Note"]
        certs = ["UPSC Civil Services Examination (CSE)", "State Public Service Commission (PSC)", "SSB Service Selection Board Clearance", "LBSNAA Officer Training Certification", "National Disaster Management Cert"]
        tools = ["e-Office Govt Workflow Portal", "GIS Geo-Spatial Mapping", "Crime & Criminal Tracking (CCTNS)", "Public Financial Management (PFMS)", "National Data & Analytics Platform"]
        top_orgs = ["Government of India", "State Civil Services Bureau", "Ministry of Home Affairs", "Indian Armed Forces", "NITI Aayog"]
        hotspots = [{"city": "New Delhi", "demand": "Very High", "reason": "Central Secretariat, Union Ministries & UPSC Headquarters."}, {"city": "State Capitals (Mumbai/Bengaluru/Lucknow)", "demand": "High", "reason": "State Secretariats, Police HQs & District Collectorates."}, {"city": "District HQs Nationwide", "demand": "High", "reason": "Field administration, public safety & revenue governance."}, {"city": "Dehradun / Mussoorie", "demand": "Moderate-High", "reason": "National Civil Services Academy & Defense Training Hubs."}, {"city": "Washington D.C. / UN HQs", "demand": "Moderate", "reason": "Diplomatic missions & international civil services."}]
        trend_skills = ["E-Governance Architecture", "Data-Driven Public Policy", "Disaster Resilience Planning", "Public Financial Transparency", "Crisis Leadership"]
        daily_plan = ["Monday: 2 hrs Indian Polity & Constitutional Law", "Tuesday: 2 hrs Current Affairs & PIB News Analysis", "Wednesday: 2 hrs Economic Policy & Budget Analysis", "Thursday: 2 hrs Ethics & Case Studies Practice", "Friday: 2 hrs Answer Writing & Essay Preparation", "Saturday: 3 hrs Mock Test & Revision", "Sunday: 1 hr Weekly Performance Review"]
    elif any(w in c_low for w in ["lawyer", "advocate", "judge", "legal", "solicitor", "paralegal"]):
        edu = "LLB / LLM (Bachelor / Master of Laws) + Bar Council Enrolment & All India Bar Examination (AIBE)"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹5.0L - ₹9.0L / yr", "₹12.0L - ₹22.0L / yr", "₹30.0L - ₹65.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$70k - $100k / yr", "$140k - $210k / yr", "$250k - $400k / yr"
        roles = [f"Junior Associate Lawyer", f"Senior Associate Advocate", f"Partner / Corporate Counsel", f"Additional District Judge", f"Senior Counsel / Magistrate"]
        sk_b = ["Legal Aptitude & Reasoning", "Constitutional & Criminal Law", "Contract & Corporate Law", "Legal Drafting & Case Summaries", "Client Consultation"]
        sk_i = ["Courtroom Advocacy & Trial Practice", "Arbitration & Dispute Resolution", "Intellectual Property & Tax Law", "Due Diligence & M&A Compliance", "Cross-Examination Techniques"]
        sk_a = ["High Court & Supreme Court Litigation", "Cross-Border Corporate Mergers", "Constitutional Bench Advocacy", "Senior Judicial Administration", "International Maritime & Trade Law"]
        yt = [{"name": "Live Law Official", "url": "https://www.youtube.com/@LiveLawOfficial"}, {"name": "Bar & Bench", "url": "https://www.youtube.com/@BarandBench"}, {"name": "Finology Legal", "url": "https://www.youtube.com/@FinologyLegal"}, {"name": "Unacademy Judiciary", "url": "https://www.youtube.com/@UnacademyJudiciary"}, {"name": "LegalEagle US Law", "url": "https://www.youtube.com/@LegalEagle"}]
        courses = [{"name": "Coursera Introduction to Key Legal Concepts", "url": "https://www.coursera.org"}, {"name": "NPTEL Corporate Law & Intellectual Property", "url": "https://nptel.ac.in"}, {"name": "Harvard Law School Online", "url": "https://online.harvard.edu"}, {"name": "edX International Law", "url": "https://www.edx.org"}, {"name": "Swayam Constitutional Law", "url": "https://swayam.gov.in"}]
        docs = [{"name": "Supreme Court of India Portal", "url": "https://main.sci.gov.in"}, {"name": "India Code Legislative Portal", "url": "https://www.indiacode.nic.in"}, {"name": "Bar Council of India", "url": "http://www.barcouncilofindia.org"}, {"name": "e-Courts India Portal", "url": "https://ecourts.gov.in"}, {"name": "UNCITRAL International Trade Law", "url": "https://uncitral.un.org"}]
        books = [{"name": "Constitution of India by D.D. Basu", "url": "https://amazon.com"}, {"name": "Ratanlal & Dhirajlal's Law of Torts", "url": "https://amazon.com"}, {"name": "Indian Penal Code by K.D. Gaur", "url": "https://amazon.com"}, {"name": "Contract Law by Avtar Singh", "url": "https://amazon.com"}, {"name": "Company Law by Avtar Singh", "url": "https://amazon.com"}]
        projs_b = ["Case Briefing Note & Legal Summary", "Drafting a Standard Non-Disclosure Agreement (NDA)", "RTI Application Drafting & Filing Simulation", "Consumer Court Complaint Petition", "Basic Legal Due Diligence Audit"]
        projs_i = ["Bail Application & Criminal Petition Drafting", "Corporate M&A Shareholders Agreement Audit", "Arbitration Statement of Claim Portfolio", "Intellectual Property Patent Infringement Analysis", "PIL Public Interest Litigation Blueprint"]
        projs_a = ["Supreme Court Special Leave Petition (SLP) Draft", "Cross-Border Commercial Contract Negotiation", "High Court Writ Petition Drafting", "Corporate Restructuring Legal Compliance", "Judicial Service Mains Answer Mock Portfolio"]
        certs = ["All India Bar Examination (AIBE) Certificate", "Judicial Services Examination Clearance", "Certified Corporate Compliance Professional", "Arbitration & Mediation Certification", "Cyber Law & IP Specialist Diploma"]
        tools = ["Manupatra & SCC Online Legal Databases", "e-Courts India Case Status Portal", "Clio Legal Practice Management", "Westlaw / LexisNexis", "Adobe Acrobat PDF Digital Signing"]
        top_orgs = ["Supreme Court of India", "AZB & Partners", "Cyril Amarchand Mangaldas", "Shardul Amarchand Mangaldas", "Khaitan & Co"]
        hotspots = [{"city": "New Delhi (Supreme Court / High Court)", "demand": "Very High", "reason": "Apex Judicial Court, Central Tribunals & Premier Law Firms."}, {"city": "Mumbai (Bombay High Court)", "demand": "Very High", "reason": "Financial Capital, Corporate Law Firms & NCLT Benches."}, {"city": "Bengaluru", "demand": "High", "reason": "Tech Startup Contracts, IP Litigation & High Court."}, {"city": "London / UK", "demand": "High", "reason": "Global Arbitrations, Common Law & Commercial Law Firms."}, {"city": "New York / USA", "demand": "High", "reason": "Wall Street Corporate Law & International Arbitration."}]
        trend_skills = ["AI Legal Research & Automation", "Cyber Law & Data Privacy (DPDP)", "ESG & Green Energy Compliance", "Cross-Border Arbitration", "Fintech Regulatory Compliance"]
        daily_plan = ["Monday: 2 hrs Constitutional & Statute Case Law", "Tuesday: 2 hrs Legal Drafting & Petition Practice", "Wednesday: 2 hrs Corporate & Contract Law Case Analysis", "Thursday: 2 hrs Judgment Summarization & Landmark Precedents", "Friday: 2 hrs Courtroom Practice & Mock Arguments", "Saturday: 3 hrs Legal Database Research & Essay Writing", "Sunday: 1 hr Weekly Progress & Bar Exam Review"]
    elif any(w in c_low for w in ["cyber", "security", "hacker", "pentest", "infosec", "soc"]):
        edu = "B.Tech / B.Sc in Computer Science, Cyber Security or IT + CEH / CISSP Certification"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.5L - ₹11.0L / yr", "₹15.0L - ₹26.0L / yr", "₹32.0L - ₹60.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$85k - $120k / yr", "$160k - $240k / yr", "$280k - $450k / yr"
        roles = ["SOC Analyst L1/L2", "Penetration Tester / Ethical Hacker", "Cyber Security Consultant", "Security Architect", "Chief Information Security Officer (CISO)"]
        sk_b = ["Linux Administration & Bash Scripting", "Networking Protocols (TCP/IP, OSI, DNS)", "Ethical Hacking Fundamentals", "Python for Automation", "OWASP Top 10 Vulnerabilities"]
        sk_i = ["SIEM Tools (Splunk, Sentinel, ELK)", "Penetration Testing (Metasploit, Burp Suite)", "Cloud Security (AWS/Azure IAM & GuardDuty)", "Digital Forensics & Incident Response (DFIR)", "Network Traffic Analysis (Wireshark)"]
        sk_a = ["Malware Reverse Engineering & Assembly", "Zero-Day Exploit Development", "Red Team Cyber Operations & Adversary Emulation", "CISO Enterprise Risk Management", "Cryptographic Architecture"]
        yt = [{"name": "NetworkChuck", "url": "https://www.youtube.com/@NetworkChuck"}, {"name": "The Cyber Mentor", "url": "https://www.youtube.com/@TheCyberMentor"}, {"name": "John Hammond", "url": "https://www.youtube.com/@JohnHammond"}, {"name": "David Bombal", "url": "https://www.youtube.com/@davidbombal"}, {"name": "LiveOverflow", "url": "https://www.youtube.com/@LiveOverflow"}]
        courses = [{"name": "TryHackMe Cyber Security Pathways", "url": "https://tryhackme.com"}, {"name": "Hack The Box Academy", "url": "https://academy.hackthebox.com"}, {"name": "Coursera Google Cybersecurity Cert", "url": "https://www.coursera.org"}, {"name": "SANS Cyber Defense Training", "url": "https://www.sans.org"}, {"name": "Cybrary IT Security", "url": "https://www.cybrary.it"}]
        docs = [{"name": "OWASP Official Security Guides", "url": "https://owasp.org"}, {"name": "NIST Cybersecurity Framework", "url": "https://www.nist.gov"}, {"name": "MITRE ATT&CK Framework", "url": "https://attack.mitre.org"}, {"name": "PortSwigger Web Security Academy", "url": "https://portswigger.net"}, {"name": "CISA Cyber Bulletins", "url": "https://www.cisa.gov"}]
        books = [{"name": "The Web Application Hacker's Handbook by Stuttard", "url": "https://amazon.com"}, {"name": "Practical Malware Analysis by Sikorski", "url": "https://amazon.com"}, {"name": "Network Attacks & Exploitation by Matthew Monte", "url": "https://amazon.com"}, {"name": "Operator Handbook: Red Team Field Manual", "url": "https://amazon.com"}, {"name": "Blue Team Handbook: Incident Response", "url": "https://amazon.com"}]
        projs_b = ["Home Lab Linux Server Hardening", "Wireshark Packet Capture Analysis", "Basic Port Scanning Script in Python", "OWASP Web App Vulnerability Scan Report", "Multi-Factor Auth Setup Guide"]
        projs_i = ["Splunk SIEM Log Monitoring & Dashboard", "Metasploit Vulnerability Exploitation Lab", "AWS Cloud Trail & GuardDuty Threat Monitoring", "Phishing Incident Simulation & Response", "Active Directory Penetration Testing Lab"]
        projs_a = ["Enterprise Red Team Campaign & Report", "Custom Malware Sandbox Reverse Engineering", "Zero-Trust Infrastructure Architecture", "Kube-Hunter Kubernetes Security Audit", "ISO 27001 Compliance Audit Framework"]
        certs = ["CompTIA Security+", "Certified Ethical Hacker (CEH)", "OSCP (Offensive Security Certified Professional)", "CISSP (Certified Information Systems Security Professional)", "CISM / CISA Certifications"]
        tools = ["Wireshark & Nmap", "Burp Suite Professional", "Metasploit Framework", "Splunk & Elastic SIEM", "Ghidra & IDA Pro"]
        top_orgs = ["Palo Alto Networks", "CrowdStrike", "Mandiant / Google Cloud Security", "Cloudflare", "Tata Consultancy Services (Cyber Div)"]
        hotspots = [{"city": "Bengaluru", "demand": "Very High", "reason": "Premier India tech R&D hub with dedicated Cyber SOC centers."}, {"city": "Washington D.C. / USA", "demand": "Very High", "reason": "US Federal Cyber Defense & Defense Contractor Hub."}, {"city": "Hyderabad", "demand": "High", "reason": "Global MNC Security Operations Centers & Telco Infrastructure."}, {"city": "London / UK", "demand": "High", "reason": "Fintech & Banking Cyber Security Infrastructure."}, {"city": "Pune", "demand": "High", "reason": "Major Automotive & IT Security Engineering Hub."}]
        trend_skills = ["AI Threat Hunting & Detection", "Cloud Security Posture Management (CSPM)", "Zero-Trust Architecture", "ICS/SCADA Operational Security", "Quantum-Safe Cryptography"]
        daily_plan = ["Monday: 2 hrs Networking & Protocol Hardening", "Tuesday: 2 hrs Web Vulnerability Scanning & Burp Suite", "Wednesday: 2 hrs TryHackMe / HTB Hands-on Lab", "Thursday: 2 hrs SIEM Log Analysis & Incident Handling", "Friday: 2 hrs Python Security Automation Scripting", "Saturday: 3 hrs CTF Challenge & Exploit Analysis", "Sunday: 1 hr Weekly Cyber Security Review"]
    elif any(w in c_low for w in ["ux", "ui", "design", "figma", "product design"]):
        edu = "B.Des / B.Sc in Interaction Design, Human-Computer Interaction (HCI), Graphic Design or Self-Taught Portfolio"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.0L - ₹10.0L / yr", "₹14.0L - ₹24.0L / yr", "₹28.0L - ₹50.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$85k - $125k / yr", "$140k - $195k / yr", "$210k - $340k / yr"
        roles = ["Junior UI/UX Designer", "Product Designer", "Senior UX Researcher", "Lead Design Systems Architect", "VP / Head of Design"]
        sk_b = ["User Research & User Personas", "Wireframing & Information Architecture", "Figma Auto-Layout & Components", "Color Theory & Typography", "Usability Testing Basics"]
        sk_i = ["Advanced Figma Design Systems", "Interactive Prototyping & Micro-Animations", "Design System Governance", "Heuristic Evaluation", "Accessibility (WCAG 2.1 Standards)"]
        sk_a = ["UX Data Analytics & A/B Test Interpretation", "Enterprise Product Strategy", "Cross-Functional Agile Design Ops", "Motion Design in Principle/Rive", "AI-Powered UX Prototyping"]
        yt = [{"name": "Figma Official", "url": "https://www.youtube.com/@Figma"}, {"name": "AJ&Smart UX", "url": "https://www.youtube.com/@AJSmart"}, {"name": "The Futur by Chris Do", "url": "https://www.youtube.com/@thefutur"}, {"name": "DesignCourse", "url": "https://www.youtube.com/@DesignCourse"}, {"name": "Mizko Product Design", "url": "https://www.youtube.com/@mizko"}]
        courses = [{"name": "Google UX Design Professional Cert", "url": "https://www.coursera.org"}, {"name": "Interaction Design Foundation (IxDF)", "url": "https://www.interaction-design.org"}, {"name": "Udemy Figma Masterclass", "url": "https://www.udemy.com"}, {"name": "Shift Nudge Typography Course", "url": "https://shiftnudge.com"}, {"name": "Nielsen Norman Group UX Certification", "url": "https://www.nngroup.com"}]
        docs = [{"name": "Nielsen Norman Group Articles", "url": "https://www.nngroup.com"}, {"name": "Material Design 3 Guidelines", "url": "https://m3.material.io"}, {"name": "Apple Human Interface Guidelines (HIG)", "url": "https://developer.apple.com/design"}, {"name": "WCAG 2.1 Web Accessibility Guidelines", "url": "https://www.w3.org/WAI"}, {"name": "Figma Help & Best Practices", "url": "https://help.figma.com"}]
        books = [{"name": "The Design of Everyday Things by Don Norman", "url": "https://amazon.com"}, {"name": "Don't Make Me Think by Steve Krug", "url": "https://amazon.com"}, {"name": "Refactoring UI by Adam Wathan", "url": "https://amazon.com"}, {"name": "Atomic Design by Brad Frost", "url": "https://amazon.com"}, {"name": "Designing Interfaces by Jenifer Tidwell", "url": "https://amazon.com"}]
        projs_b = ["Mobile E-Commerce App Redesign Case Study", "Figma UI Kit & Icon Library", "User Persona & Journey Map Portfolio", "Accessibility Audit of Public Website", "Landing Page Layout & Typography Study"]
        projs_i = ["SaaS Dashboard UI/UX Design System", "Fintech Mobile Wallet Interactive Prototype", "Usability Testing Video Summary & Audit", "Design Token Library in Figma", "Micro-Animation Interaction Study"]
        projs_a = ["Complex Multi-Platform Enterprise UI Architecture", "AI-Powered Product UX Case Study", "Global E-Commerce Checkout Flow Optimization", "Design System Governance Documentation", "Design Sprint Facilitation Guide"]
        certs = ["Google UX Design Professional Certificate", "Nielsen Norman Group UX Master Cert", "Certified Usability Analyst (CUA)", "Interaction Design Foundation Certificate", "Meta Front-End Developer & UI Cert"]
        tools = ["Figma & FigJam", "Adobe XD & Illustrator", "Principle / Framer / Rive", "Miro & Notion for UX Research", "LottieFiles & Maze Usability"]
        top_orgs = ["Airbnb", "Apple Product Design", "Google Material UX", "Figma Design Team", "Swiggy / Zomato Design Labs"]
        hotspots = [{"city": "Bengaluru", "demand": "Very High", "reason": "India SaaS & consumer product design capital."}, {"city": "San Francisco / Silicon Valley", "demand": "Very High", "reason": "Global product design & venture-backed tech startups."}, {"city": "Mumbai", "demand": "High", "reason": "Fintech & media product design hub."}, {"city": "London / UK", "demand": "High", "reason": "European design agencies & fintech product labs."}, {"city": "Berlin / Germany", "demand": "High", "reason": "Vibrant European startup & digital product design scene."}]
        trend_skills = ["AI-Assisted UX Prototyping", "Design Tokens & Token Studio", "3D & Spatial UI (VisionOS)", "Voice & Conversational UX", "Micro-Interactions in Rive"]
        daily_plan = ["Monday: 2 hrs User Research & Competitor Analysis", "Tuesday: 2 hrs Figma Wireframing & Layout Design", "Wednesday: 2 hrs Component Building & Design System", "Thursday: 2 hrs Usability Testing & Feedback Iteration", "Friday: 2 hrs High-Fidelity Prototyping & Motion", "Saturday: 3 hrs Case Study Writing & Portfolio Polish", "Sunday: 1 hr Weekly Design Critique Review"]
    elif any(w in c_low for w in ["finance", "banker", "investor", "investment", "fintech", "accountant", "ca", "cfa"]):
        edu = "B.Com / BBA in Finance, CA (Chartered Accountant), CFA (Chartered Financial Analyst), or MBA Finance"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹7.0L - ₹12.0L / yr", "₹16.0L - ₹28.0L / yr", "₹35.0L - ₹70.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$80k - $115k / yr", "$135k - $185k / yr", "$195k - $320k / yr"
        roles = ["Financial Analyst / Junior Accountant", "Investment Banking Associate", "Senior Financial Controller", "Portfolio Manager", "Chief Financial Officer (CFO)"]
        sk_b = ["Financial Accounting & Bookkeeping", "Excel Financial Modeling (VLOOKUP, Pivot Tables)", "Corporate Finance Principles", "Financial Statement Analysis", "Business Mathematics"]
        sk_i = ["DCF Valuation & LBO Modeling", "Equity Research & Portfolio Analysis", "Financial Risk Management", "Taxation & Statutory Audit", "Bloomberg Terminal Navigation"]
        sk_a = ["Cross-Border Mergers & Acquisitions (M&A)", "Venture Capital Due Diligence", "Algorithmic Trading Strategies", "Corporate Treasury & FX Hedging", "CFO Enterprise Financial Governance"]
        yt = [{"name": "Wall Street Prep", "url": "https://www.youtube.com/@WallStreetPrep"}, {"name": "Aswath Damodaran (Valuation Guru)", "url": "https://www.youtube.com/@AswathDamodaranonValuation"}, {"name": "CFA Institute", "url": "https://www.youtube.com/@CFAInstitute"}, {"name": "The Plain Bagel", "url": "https://www.youtube.com/@ThePlainBagel"}, {"name": "CA Rachana Ranade", "url": "https://www.youtube.com/@CARachanaRanade"}]
        courses = [{"name": "CFA Level 1 Preparation Program", "url": "https://www.cfainstitute.org"}, {"name": "Coursera Wharton Financial Markets", "url": "https://www.coursera.org"}, {"name": "Wall Street Prep Financial Modeling", "url": "https://www.wallstreetprep.com"}, {"name": "NPTEL Financial Accounting & Analysis", "url": "https://nptel.ac.in"}, {"name": "edX Corporate Finance", "url": "https://www.edx.org"}]
        docs = [{"name": "SEC EDGAR Database (US Filings)", "url": "https://www.sec.gov/edgar"}, {"name": "RBI Official Notifications & Reports", "url": "https://www.rbi.org.in"}, {"name": "IFRS Accounting Standards Portal", "url": "https://www.ifrs.org"}, {"name": "NSE India Market Data", "url": "https://www.nseindia.com"}, {"name": "Investopedia Financial Glossary", "url": "https://www.investopedia.com"}]
        books = [{"name": "The Intelligent Investor by Benjamin Graham", "url": "https://amazon.com"}, {"name": "Corporate Finance by Ross, Westerfield, Jaffe", "url": "https://amazon.com"}, {"name": "Investment Valuation by Aswath Damodaran", "url": "https://amazon.com"}, {"name": "Financial Shenanigans by Howard Schilit", "url": "https://amazon.com"}, {"name": "Principles of Corporate Finance by Brealey Myers", "url": "https://amazon.com"}]
        projs_b = ["Three-Financial-Statement Excel Model", "Public Company Ratio Analysis Report", "Personal Wealth & Tax Optimization Plan", "Company Annual Report Analysis", "Stock Portfolio Tracking Spreadsheet"]
        projs_i = ["DCF Valuation Model of Tech Company", "Mergers & Acquisitions (M&A) Pitch Deck", "Credit Risk Assessment Portfolio", "Automated Python Stock Analysis Script", "Corporate Budget Variance Report"]
        projs_a = ["LBO Leveraged Buyout Financial Model", "Global FX Hedging Strategy Blueprint", "Venture Capital Deal Term Sheet Audit", "Enterprise Risk & Capital Allocation Strategy", "IPO Valuation & Prospectus Review"]
        certs = ["Chartered Financial Analyst (CFA)", "Chartered Accountant (CA)", "Financial Risk Manager (FRM)", "Certified Public Accountant (CPA)", "NCFM Financial Markets Certifications"]
        tools = ["Microsoft Excel (Advanced VBA/Macros)", "Bloomberg Terminal & Capital IQ", "Power BI / Tableau for Finance", "QuickBooks & Tally Prime", "Python / R for Quantitative Finance"]
        top_orgs = ["Goldman Sachs", "J.P. Morgan Chase", "Morgan Stanley", "HDFC Bank / ICICI Bank", "Deloitte / PwC / EY / KPMG"]
        hotspots = [{"city": "Mumbai (BKC / Nariman Point)", "demand": "Very High", "reason": "Financial capital of India, RBI & investment banking HQs."}, {"city": "New York / Wall Street", "demand": "Very High", "reason": "Global financial center & investment banking capital."}, {"city": "London / UK", "demand": "Very High", "reason": "European financial capital & FX trading hub."}, {"city": "Bengaluru", "demand": "High", "reason": "Fintech startup capital & corporate finance centers."}, {"city": "Singapore / UAE", "demand": "High", "reason": "Asian & Middle Eastern wealth management & banking hub."}]
        trend_skills = ["AI-Driven Financial Forecasting", "Fintech API Integration", "Algorithmic Python Trading", "ESG Financial Auditing", "Decentralized Finance (DeFi) Risk"]
        daily_plan = ["Monday: 2 hrs Financial Accounting & Statement Analysis", "Tuesday: 2 hrs Excel Financial Modeling & DCF Practice", "Wednesday: 2 hrs Corporate Finance Case Studies", "Thursday: 2 hrs Stock Valuation & Ratio Analysis", "Friday: 2 hrs CFA / CA Exam Preparation", "Saturday: 3 hrs Bloomberg Data Research & Report Writing", "Sunday: 1 hr Weekly Market Summary & Review"]
    elif any(w in c_low for w in ["chef", "culinary", "cook", "bakery", "hotel management"]):
        edu = "B.Sc in Hospitality & Culinary Arts / Diploma in Bakery & Pastry Arts + Kitchen Apprenticeship"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹4.5L - ₹7.5L / yr", "₹10.5L - ₹18.0L / yr", "₹22.0L - ₹42.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$45k - $65k / yr", "$75k - $110k / yr", "$120k - $220k / yr"
        roles = ["Commis Chef (Line Cook)", "Chef de Partie (Station Chef)", "Sous Chef (Second in Command)", "Executive Chef (Head Chef)", "Culinary Director / Restaurant Owner"]
        sk_b = ["Knife Skills & Basic Cuts", "Food Safety & Hygiene (HACCP Standards)", "Stock & Sauce Foundations (Mother Sauces)", "Kitchen Station Management", "Ingredient Identification"]
        sk_i = ["Advanced Pastry & Baking Techniques", "Menu Engineering & Food Costing", "Sous-Vide & Modernist Cooking", "Plating & Visual Presentation", "Kitchen Inventory Control"]
        sk_a = ["Michelin-Level Menu Concept Design", "Large-Scale Banquet & Catering Management", "Restaurant P&L & Labor Cost Optimization", "Culinary R&D & Flavor Chemistry", "Enterprise Kitchen Leadership"]
        yt = [{"name": "Gordon Ramsay", "url": "https://www.youtube.com/@gordonramsay"}, {"name": "French Cooking Academy", "url": "https://www.youtube.com/@FrenchCookingAcademy"}, {"name": "MasterChef Official", "url": "https://www.youtube.com/@MasterChefWorld"}, {"name": "Babas Kitchen & Culinary", "url": "https://www.youtube.com/@BabasKitchen"}, {"name": "Eater Culinary Channel", "url": "https://www.youtube.com/@eater"}]
        courses = [{"name": "Rouxbe Online Culinary School", "url": "https://rouxbe.com"}, {"name": "Coursera Food & Beverage Management", "url": "https://www.coursera.org"}, {"name": "Le Cordon Bleu Online Diploma", "url": "https://www.cordonbleu.edu"}, {"name": "edX Food & Science Fundamentals", "url": "https://www.edx.org"}, {"name": "Culinary Institute of America Online", "url": "https://www.ciachef.edu"}]
        docs = [{"name": "FSSAI Food Safety Guidelines", "url": "https://www.fssai.gov.in"}, {"name": "FDA Food Code Portal", "url": "https://www.fda.gov"}, {"name": "HACCP Food Safety Manual", "url": "https://www.haccpbuilder.com"}, {"name": "Michelin Guide Official Portal", "url": "https://guide.michelin.com"}, {"name": "World Chefs Association Standards", "url": "https://worldchefs.org"}]
        books = [{"name": "The Professional Chef by Culinary Institute of America", "url": "https://amazon.com"}, {"name": "On Food and Cooking by Harold McGee", "url": "https://amazon.com"}, {"name": "Le Repertoire de la Cuisine by Louis Saulnier", "url": "https://amazon.com"}, {"name": "The Flavor Bible by Karen Page", "url": "https://amazon.com"}, {"name": "Modernist Cuisine by Nathan Myhrvold", "url": "https://amazon.com"}]
        projs_b = ["5-Mother Sauces Execution Portfolio", "Kitchen HACCP Hygiene Compliance Audit", "Knife Skill Speed & Accuracy Logbook", "Basic Recipe Costing Spreadsheet", "Food Inventory Control Log"]
        projs_i = ["Seasonal 4-Course Tasting Menu Design", "Pastry & Artisan Bread Baking Portfolio", "Restaurant Food Waste Reduction Plan", "Sous-Vide Cooking Temperature Guide", "Kitchen Station Workflow Optimization"]
        projs_a = ["Michelin-Style Restaurant Concept Blueprint", "Banquet Event 500-Pax Catering Masterplan", "Complete Kitchen P&L & Food Costing Strategy", "Culinary Fusion Recipe Development", "Executive Chef Kitchen Operations Manual"]
        certs = ["ServSafe Food Handler & Manager Cert", "HACCP Food Safety Specialist Certification", "Certified Executive Chef (CEC)", "City & Guilds Culinary Arts Diploma", "FSSAI Food Safety Supervisor Cert"]
        tools = ["Professional Chef Knife Set (Gyuto/Paring)", "Sous-Vide Precision Cooker", "Combitherm Ovens & Induction Ranges", "Kitchen Inventory Software (MarketMan)", "Thermal Plating & Pastry Tools"]
        top_orgs = ["Taj Hotels / Oberoi Group", "Marriott International", "The Ritz-Carlton", "Michelin-Starred Restaurants", "Cruise Line Culinary Fleets"]
        hotspots = [{"city": "Mumbai", "demand": "Very High", "reason": "India culinary capital with luxury hotels & fine dining."}, {"city": "Paris / France", "demand": "Very High", "reason": "Global gastronomy capital & French culinary heritage."}, {"city": "New York / USA", "demand": "Very High", "reason": "Diverse fine dining scene & Michelin restaurants."}, {"city": "Dubai / UAE", "demand": "High", "reason": "Luxury resort hospitality & global celebrity chef venues."}, {"city": "Goa / Bengaluru", "demand": "High", "reason": "Thriving boutique restaurant & artisanal cafe culture."}]
        trend_skills = ["Plant-Based & Vegan Culinary R&D", "Zero-Waste Kitchen Management", "Fermentation & Foraging", "Sous-Vide Precision Cooking", "Digital Food Costing Tech"]
        daily_plan = ["Monday: 2 hrs Knife Practice & Basic Culinary Techniques", "Tuesday: 2 hrs Recipe Development & Sauce Execution", "Wednesday: 2 hrs Food Safety & HACCP Protocol Study", "Thursday: 2 hrs Menu Engineering & Recipe Costing", "Friday: 2 hrs Fine Dining Plating & Presentation Practice", "Saturday: 3 hrs Kitchen Apprenticeship & Station Service", "Sunday: 1 hr Weekly Culinary Review"]
    else:
        edu = "Relevant Bachelor's / Master's Degree or Industry Certification Track"
        dyn_sal_ind = get_career_salary_benchmark(career, "India")
        dyn_sal_cnt = get_career_salary_benchmark(career, country or "Global")
        sal_ind_f, sal_ind_m, sal_ind_s = dyn_sal_ind["fresher"], dyn_sal_ind["mid"], dyn_sal_ind["senior"]
        sal_cnt_f, sal_cnt_m, sal_cnt_s = dyn_sal_cnt["fresher"], dyn_sal_cnt["mid"], dyn_sal_cnt["senior"]
        roles = [f"Junior {c_title}", f"Mid-Level {c_title}", f"Senior {c_title}", f"Lead Specialist {c_title}", f"Director / Executive {c_title}"]
        sk_b = [f"Foundations of {c_title}", f"Core Principles & Methodologies", f"Essential Industry Tools for {c_title}", "Professional Communication & Workflow", f"Basic Case Studies in {c_title}"]
        sk_i = [f"Advanced Operations in {c_title}", "Data Analytics & Performance Metrics", f"Cross-Functional Project Management", f"Quality Control & Standards in {c_title}", f"Specialized Software & Tooling"]
        sk_a = [f"Enterprise Strategy for {c_title}", "Team Leadership & Resource Allocation", f"Regulatory Compliance & Risk Governance", f"Strategic Innovation in {c_title}", f"Executive Management & Advisory"]
        yt = [{"name": "Harvard Business Review", "url": "https://www.youtube.com/@harvardbusinessreview"}, {"name": "MIT OpenCourseWare", "url": "https://www.youtube.com/@mitocw"}, {"name": "TED Talks Official", "url": "https://www.youtube.com/@TED"}, {"name": "Google Career Certificates", "url": "https://www.youtube.com/@google"}, {"name": "Coursera Official", "url": "https://www.youtube.com/@coursera"}]
        courses = [{"name": "Coursera Professional Specialization", "url": "https://www.coursera.org"}, {"name": "edX Professional Certificate", "url": "https://www.edx.org"}, {"name": "Udemy Executive Masterclass", "url": "https://www.udemy.com"}, {"name": "NPTEL Industry Certification", "url": "https://nptel.ac.in"}, {"name": "Swayam Executive Learning", "url": "https://swayam.gov.in"}]
        docs = [{"name": "ISO International Standards Portal", "url": "https://www.iso.org"}, {"name": "Harvard Business School Research", "url": "https://hbswk.hbs.edu"}, {"name": "McKinsey Insights Portal", "url": "https://www.mckinsey.com"}, {"name": "Gartner Industry Reports", "url": "https://www.gartner.com"}, {"name": "IEEE Xplore Digital Library", "url": "https://ieeexplore.ieee.org"}]
        books = [{"name": "The Personal MBA by Josh Kaufman", "url": "https://amazon.com"}, {"name": "Deep Work by Cal Newport", "url": "https://amazon.com"}, {"name": "Atomic Habits by James Clear", "url": "https://amazon.com"}, {"name": "Good to Great by Jim Collins", "url": "https://amazon.com"}, {"name": "Thinking, Fast and Slow by Daniel Kahneman", "url": "https://amazon.com"}]
        projs_b = [f"{c_title} Operational Workflow Audit", f"Foundational Case Study Report in {c_title}", f"Tooling & Process Standardization Project", f"Basic Quality Assessment Checklist", f"Entry-Level Milestone Project"]
        projs_i = [f"{c_title} System Optimization & Case Study", f"Data-Driven Performance Dashboard", f"Cross-Functional Team Project Execution", f"Process Automation & Tool Integration", f"Intermediate Milestone Project"]
        projs_a = [f"Enterprise Transformation Blueprint for {c_title}", f"Strategic Risk & Compliance Audit", f"Executive Level Master Project", f"Global Operational Scaling Strategy", f"Senior Leadership Capstone Project"]
        certs = [f"Certified {c_title} Professional (CPP)", f"Industry Association Specialist Certification", f"Project Management Professional (PMP)", f"Advanced Executive Diploma in {c_title}", f"Global Standards Accreditation Certificate"]
        tools = [f"Primary Software Suite for {c_title}", "Enterprise Resource Planning (ERP)", "Data Analytics & Reporting Tools", "Project Collaboration & Workflow Apps", "Quality Assurance & Testing Frameworks"]
        top_orgs = ["Global Market Leaders", "Fortune 500 Enterprises", "Premier National Organizations", "Top Tier Consulting Firms", "Leading Specialty Industry Firms"]
        hotspots = [{"city": "Bengaluru / India", "demand": "Very High", "reason": "Leading tech, corporate & industrial hub."}, {"city": "New York / USA", "demand": "Very High", "reason": "Global corporate & financial headquarters."}, {"city": "London / UK", "demand": "High", "reason": "European corporate & financial center."}, {"city": "Singapore", "demand": "High", "reason": "Asia-Pacific business & innovation hub."}, {"city": "Mumbai / India", "demand": "High", "reason": "National commercial & corporate capital."}]
        trend_skills = [f"AI & Automation Integration in {c_title}", "Data-Driven Decision Making", "Agile Project Execution", "Sustainability & ESG Governance", "Strategic Executive Leadership"]
        daily_plan = ["Monday: 2 hrs Core Principles & Industry Fundamentals", "Tuesday: 2 hrs Practical Tooling & Hands-on Practice", "Wednesday: 2 hrs Case Studies & System Architecture", "Thursday: 2 hrs Portfolio & Project Execution", "Friday: 2 hrs Quality Audit & Process Refactoring", "Saturday: 3 hrs Mock Test & Professional Case Review", "Sunday: 1 hr Weekly Self-Assessment & Career Strategy"]

    # Sector Classification
    if any(w in c_low for w in ["doctor", "surgeon", "physician", "dentist", "nurse", "medical", "pharmacist"]):
        edu = "MBBS / MD / BDS / Nursing Degree + Clinical Internship & Medical Council Registration"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.0L - ₹10.0L / yr", "₹15.0L - ₹28.0L / yr", "₹35.0L - ₹75.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$75k - $110k / yr", "$150k - $240k / yr", "$280k - $450k / yr"
        roles = [f"Resident {c_title}", f"Junior Consultant {c_title}", f"Senior Consultant {c_title}", f"Head of Clinical Department", f"Medical Director"]
        sk_b = ["Human Anatomy & Physiology", "Medical Terminology", "Vital Signs & Triage", "First Aid & CPR", "Patient Empathy"]
        sk_i = ["Clinical Pharmacology", "Pathology & Diagnostics", "EMR/EHR Systems (Epic/Cerner)", "Emergency Resuscitation", "Surgical Hygiene"]
        sk_a = ["Advanced Surgical Protocols", "Critical ICU Management", "Complex Differential Diagnosis", "Clinical Research & Publishing", "Hospital Governance"]
        yt = [{"name": "Osmosis by Elseveir", "url": "https://www.youtube.com/@osmosis"}, {"name": "Ninja Nerd - Medicine", "url": "https://www.youtube.com/@NinjaNerdOfficial"}, {"name": "Doctor Mike", "url": "https://www.youtube.com/@DoctorMike"}, {"name": "Armando Hasudungan", "url": "https://www.youtube.com/@armandohasudungan"}, {"name": "Khan Academy Medicine", "url": "https://www.youtube.com/@khanacademy"}]
        courses = [{"name": "Harvard Medical School Online", "url": "https://online-learning.harvard.edu"}, {"name": "Coursera Clinical Medicine", "url": "https://www.coursera.org"}, {"name": "Stanford Health & Medicine", "url": "https://online.stanford.edu"}, {"name": "edX Anatomy & Physiology", "url": "https://www.edx.org"}, {"name": "Lecturio Medical Education", "url": "https://www.lecturio.com"}]
        docs = [{"name": "WHO Clinical Guidelines", "url": "https://www.who.int"}, {"name": "PubMed Central Literature", "url": "https://pmc.ncbi.nlm.nih.gov"}, {"name": "UpToDate Clinical Decision Support", "url": "https://www.uptodate.com"}, {"name": "CDC Health Protocols", "url": "https://www.cdc.gov"}, {"name": "ICMR Guidelines", "url": "https://www.icmr.gov.in"}]
        books = [{"name": "Harrison's Principles of Internal Medicine", "url": "https://amazon.com"}, {"name": "Gray's Anatomy for Students", "url": "https://amazon.com"}, {"name": "Robbins & Cotran Pathologic Basis of Disease", "url": "https://amazon.com"}, {"name": "Katzung Basic & Clinical Pharmacology", "url": "https://amazon.com"}, {"name": "Oxford Handbook of Clinical Medicine", "url": "https://amazon.com"}]
        projs_b = ["Patient Case Logbook Analysis", "Vital Signs Monitoring Study", "Pharmacology Dosage Calculation Chart", "First Aid Emergency Plan", "Basic Clinical Hygiene Audit"]
        projs_i = ["Diagnostic Case Study Portfolio", "EHR Clinical Workflow Design", "Hospital Ward Infection Control Audit", "Pharmacovigilance Adverse Event Study", "Emergency ICU Triage Simulation"]
        projs_a = ["Clinical Research Trial Design", "Complex Surgical Case Study Publication", "Hospital Departmental EMR System Upgrade", "Public Health Epidemic Response Protocol", "Medical Ethics Case Review"]
        certs = ["ACLS & BLS Certification", "Medical Board Registration / USMLE", "NEET PG / PLAB Specialist License", "Certified Electronic Health Record Specialist", "Critical Care Medicine Diploma"]
        tools = ["Diagnostic Stethoscope & Otoscope", "Epic / Cerner EMR Systems", "Medical Pulse Oximeter & ECG", "Surgical Instrument Set", "UpToDate Clinical Database"]
        top_orgs = ["Mayo Clinic", "AIIMS New Delhi", "Johns Hopkins Hospital", "NHS UK", "Apollo Hospitals"]
        hotspots = [{"city": "Delhi NCR", "demand": "Very High", "reason": "National premier medical institutes & super-specialty hospitals."}, {"city": "Boston / USA", "demand": "High", "reason": "Global hub for clinical research & Harvard teaching hospitals."}, {"city": "Mumbai", "demand": "High", "reason": "Leading private hospital networks & medical research hubs."}, {"city": "London / UK", "demand": "High", "reason": "NHS tertiary referral centers & medical universities."}, {"city": "Bengaluru", "demand": "Moderate-High", "reason": "Growing health-tech & multi-specialty hospital infrastructure."}]
        trend_skills = ["Robotic Surgery Protocols", "Digital EMR Data Analysis", "Telemedicine Consultation", "Precision Diagnostics", "Genomic Medicine"]
        daily_plan = ["Monday: 2 hrs Anatomy & Pathophysiology Deep Dive", "Tuesday: 2 hrs Clinical Case Study Analysis", "Wednesday: 2 hrs Pharmacology & Drug Interaction Review", "Thursday: 2 hrs EMR Documentation & Patient Simulation", "Friday: 2 hrs Clinical Rotations & Case Reviews", "Saturday: 3 hrs Diagnostic Rounds & Journal Review", "Sunday: 1 hr Weekly Medical Knowledge Assessment"]
    elif any(w in c_low for w in ["brihanmumbai", "bmc", "mcgm", "municipal", "civic"]):
        edu = "Degree / Diploma in Civil, Mechanical, Electrical Engineering or Public Administration + BMC / MPSC Selection Exam"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.0L - ₹9.5L / yr", "₹12.0L - ₹18.0L / yr", "₹22.0L - ₹38.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$60k - $85k / yr", "$95k - $130k / yr", "$150k - $210k / yr"
        roles = ["BMC Sub-Engineer / Junior Engineer", "BMC Assistant Engineer (AE)", "BMC Executive Engineer (EE)", "BMC Deputy Municipal Commissioner (DMC)", "BMC Additional Municipal Commissioner / Municipal Commissioner"]
        sk_b = ["Mumbai Municipal Corporation Act (MMC Act 1888)", "Development Control & Promotion Regulations (DCPR 2034)", "Civil Engineering & Urban Infrastructure", "BMC e-Tendering & Public Procurement", "Public Health & Solid Waste Management (SWM)"]
        sk_i = ["BMC Water Supply Engineering (Bhandup Complex / Vaitarna)", "Disaster Management & Monsoon Flood Control (1916 Control Room)", "Building Proposal Department (BP Dept) Approvals", "AutoCAD & GIS Urban Mapping", "Sewerage Operations & Environmental Engineering"]
        sk_a = ["Civic Megaproject Execution (Coastal Road / Trans-Harbour Link)", "Municipal Budgeting & Revenue Audit", "Inter-Departmental Municipal Governance", "Urban Resilience & Climate Adaptation", "Cabinet & Standing Committee Governance"]
        yt = [{"name": "StudyIQ Civil Services & MPSC", "url": "https://www.youtube.com/@StudyIQEducation"}, {"name": "Infinity Engineering Academy", "url": "https://www.youtube.com/@InfinityEngineeringAcademy"}, {"name": "Ignite Academy Maharashtra", "url": "https://www.youtube.com/@IgniteAcademy"}, {"name": "Testbook MPSC & Civil Exams", "url": "https://www.youtube.com/@TestbookMPSC"}, {"name": "Sansad TV Urban Governance", "url": "https://www.youtube.com/@SansadTV"}]
        courses = [{"name": "Swayam Urban Governance & Municipal Infrastructure", "url": "https://swayam.gov.in"}, {"name": "NPTEL Urban Planning & Civil Engineering", "url": "https://nptel.ac.in"}, {"name": "Coursera Smart Cities & Urban Policy", "url": "https://www.coursera.org"}, {"name": "YASHADA Maharashtra Public Administration", "url": "https://yashada.org"}, {"name": "edX Sustainable Urban Infrastructure", "url": "https://www.edx.org"}]
        docs = [{"name": "BMC (MCGM) Official Portal", "url": "https://www.mcgm.gov.in"}, {"name": "Mumbai Municipal Corporation Act 1888", "url": "https://legislative.gov.in"}, {"name": "DCPR 2034 Development Control Regulations", "url": "https://portal.mcgm.gov.in"}, {"name": "Maharashtra Urban Development Department", "url": "https://urban.maharashtra.gov.in"}, {"name": "National Urban Infrastructure Guidelines", "url": "https://mohua.gov.in"}]
        books = [{"name": "Mumbai Municipal Corporation Act, 1888 Handbook", "url": "https://amazon.com"}, {"name": "Urban Planning and Infrastructure in India by Kulwant Singh", "url": "https://amazon.com"}, {"name": "Civil Engineering Objective Book by R.S. Khurmi", "url": "https://amazon.com"}, {"name": "Development Control Regulations (DCPR 2034) Manual", "url": "https://amazon.com"}, {"name": "Public Administration in India by A. Avasthi", "url": "https://amazon.com"}]
        projs_b = ["BMC Ward Level Public Grievance Audit", "DCPR 2034 Floor Space Index (FSI) Calculation", "Basic Drainage & Pothole Repair Audit", "BMC e-Tender Document Review", "Solid Waste Segregation Plan"]
        projs_i = ["BMC Pumping Station & Stormwater Drainage Audit", "Building Proposal Approval Checklist & Plan Audit", "Bhandup Water Treatment Plant Flow Analysis", "Disaster Management Monsoon Preparedness Plan", "Road Concreting Quality Control Audit"]
        projs_a = ["Mumbai Coastal Road Infrastructure Resilience Review", "State-Level Municipal Solid Waste Management Masterplan", "BMC e-Governance & Single Window Property Tax System", "Suburban Sewerage Network Upgrade Blueprint", "Municipal Standing Committee Budget Proposal"]
        certs = ["BMC Junior Engineer / Assistant Engineer Recruitment Cert", "MPSC Civil Engineering Services Qualification", "Certified AutoDesk AutoCAD / Revit Professional", "Certified GIS Urban Planner", "National Institute of Urban Affairs Cert"]
        tools = ["AutoCAD & Civil 3D", "GIS Geo-Spatial Mapping", "BMC AutoDCR / e-Step Online Plan Approval", "SAP Municipal Resource Planning", "e-Procurement Portal (Mahatenders / BMC)"]
        top_orgs = ["Brihanmumbai Municipal Corporation (BMC)", "MMRDA (Mumbai Metropolitan Region Dev Authority)", "CIDCO Maharashtra", "MHADA", "Maharashtra Water Resources Department"]
        hotspots = [{"city": "Mumbai (BMC Headquarters / Fort)", "demand": "Very High", "reason": "Central Municipal Head Office, Standing Committee & Departmental HQs."}, {"city": "Suburban Mumbai Wards (Andheri/Borivali/Kurla)", "demand": "Very High", "reason": "Major Ward Offices, Building Proposal & Infrastructure Operations."}, {"city": "Navi Mumbai & Thane", "demand": "High", "reason": "Neighboring Municipal Corporations (NMMC/TMC) & Infrastructure."}, {"city": "Pune Municipal Corporation (PMC)", "demand": "High", "reason": "Major Urban Civic Body & Smart City Infrastructure Projects."}, {"city": "Nagpur & Nashik", "demand": "High", "reason": "Key Municipal Infrastructure & Urban Governance Centers."}]
        trend_skills = ["AutoDCR Digital Plan Approvals", "GIS Geo-Spatial Urban Planning", "Monsoon Flood Telemetry & Sensors", "E-Tendering & Public Procurement", "Climate Resilience & Urban Green Tech"]
        daily_plan = ["Monday: 2 hrs MMC Act 1888 & Municipal Regulations", "Tuesday: 2 hrs Civil / Mechanical Technical Subjects Study", "Wednesday: 2 hrs DCPR 2034 Development Control Rules & FSI", "Thursday: 2 hrs BMC e-Tender & AutoDCR Case Studies", "Friday: 2 hrs Previous Year BMC JE / AE Exam Questions", "Saturday: 3 hrs Mock Test & General Knowledge Revision", "Sunday: 1 hr Weekly Progress & Civic Law Review"]
    elif any(w in c_low for w in ["ias", "ips", "upsc", "police", "army", "navy", "air force", "nda", "civil servant", "government"]):
        edu = "Bachelor's Degree in any discipline + UPSC / State Public Service / SSB Selection Board Qualification"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹7.0L - ₹11.0L / yr", "₹14.0L - ₹22.0L / yr", "₹25.0L - ₹40.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$65k - $95k / yr", "$100k - $140k / yr", "$160k - $220k / yr"
        roles = [f"Assistant Magistrate / Probationary Officer", f"Sub-Divisional Magistrate / SP", f"District Collector / DIG", f"Joint Secretary / Inspector General", f"Chief Secretary / Director General of Police"]
        sk_b = ["Indian Polity & Constitution", "Indian History & Culture", "Geography & Environment", "Basic General Mental Ability", "Ethics & Integrity"]
        sk_i = ["Public Administration & Governance", "Economic & Social Development", "Internal Security & Disaster Management", "District Legal Frameworks", "Policy Drafting"]
        sk_a = ["International Relations & Strategy", "Cabinet-Level Policy Formulation", "Crisis Management & Law Enforcement", "Inter-Departmental Coordination", "Public Audit & Budgeting"]
        yt = [{"name": "StudyIQ IAS", "url": "https://www.youtube.com/@StudyIQEducation"}, {"name": "Unacademy UPSC", "url": "https://www.youtube.com/@UnacademyUPSC"}, {"name": "Vision IAS", "url": "https://www.youtube.com/@VisionIASdelhi"}, {"name": "Drishti IAS", "url": "https://www.youtube.com/@DrishtiIASvideos"}, {"name": "Sansad TV Official", "url": "https://www.youtube.com/@SansadTV"}]
        courses = [{"name": "Swayam Public Administration", "url": "https://swayam.gov.in"}, {"name": "NPTEL Governance & Policy", "url": "https://nptel.ac.in"}, {"name": "Coursera Global Public Policy", "url": "https://www.coursera.org"}, {"name": "IGNOU Public Governance", "url": "http://www.ignou.ac.in"}, {"name": "EdX International Relations", "url": "https://www.edx.org"}]
        docs = [{"name": "Constitution of India Portal", "url": "https://legislative.gov.in"}, {"name": "PIB (Press Information Bureau)", "url": "https://pib.gov.in"}, {"name": "NITI Aayog Official Reports", "url": "https://www.niti.gov.in"}, {"name": "Economic Survey of India", "url": "https://www.indiabudget.gov.in"}, {"name": "State Gazette Portal", "url": "https://egazette.gov.in"}]
        books = [{"name": "Indian Polity by M. Laxmikanth", "url": "https://amazon.com"}, {"name": "India's Struggle for Independence by Bipan Chandra", "url": "https://amazon.com"}, {"name": "Certificate Physical Geography by GC Leong", "url": "https://amazon.com"}, {"name": "Ethics, Integrity and Aptitude by Subba Rao", "url": "https://amazon.com"}, {"name": "Indian Economy by Ramesh Singh", "url": "https://amazon.com"}]
        projs_b = ["District Socio-Economic Profile Study", "Constitutional Rights Summary Report", "Local Sanitation Policy Review", "Basic Disaster Response Plan", "Public Grievance Redressal Audit"]
        projs_i = ["Urban Smart City Infrastructure Policy", "Rural Employment Scheme Implementation Audit", "District Crime Trend Analysis & Mitigation", "Environmental Impact Assessment", "Public Distribution System Optimization"]
        projs_a = ["State-Level Disaster Resilience Framework", "National E-Governance Policy Architecture", "Border Security & Inter-Agency Coordination Plan", "Fiscal Policy Reform Memorandum", "Cabinet Briefing Note"]
        certs = ["UPSC Civil Services Examination (CSE)", "State Public Service Commission (PSC)", "SSB Service Selection Board Clearance", "LBSNAA Officer Training Certification", "National Disaster Management Cert"]
        tools = ["e-Office Govt Workflow Portal", "GIS Geo-Spatial Mapping", "Crime & Criminal Tracking (CCTNS)", "Public Financial Management (PFMS)", "National Data & Analytics Platform"]
        top_orgs = ["Government of India", "State Civil Services Bureau", "Ministry of Home Affairs", "Indian Armed Forces", "NITI Aayog"]
        hotspots = [{"city": "New Delhi", "demand": "Very High", "reason": "Central Secretariat, Union Ministries & UPSC Headquarters."}, {"city": "State Capitals (Mumbai/Bengaluru/Lucknow)", "demand": "High", "reason": "State Secretariats, Police HQs & District Collectorates."}, {"city": "District HQs Nationwide", "demand": "High", "reason": "Field administration, public safety & revenue governance."}, {"city": "Dehradun / Mussoorie", "demand": "Moderate-High", "reason": "National Civil Services Academy & Defense Training Hubs."}, {"city": "Washington D.C. / UN HQs", "demand": "Moderate", "reason": "Diplomatic missions & international civil services."}]
        trend_skills = ["E-Governance Architecture", "Data-Driven Public Policy", "Disaster Resilience Planning", "Public Financial Transparency", "Crisis Leadership"]
        daily_plan = ["Monday: 2 hrs Indian Polity & Constitutional Law", "Tuesday: 2 hrs Current Affairs & PIB News Analysis", "Wednesday: 2 hrs Economic Policy & Budget Analysis", "Thursday: 2 hrs Ethics & Case Studies Practice", "Friday: 2 hrs Answer Writing & Essay Preparation", "Saturday: 3 hrs Mock Test & Revision", "Sunday: 1 hr Weekly Performance Review"]
    elif any(w in c_low for w in ["lawyer", "advocate", "judge", "legal", "solicitor", "paralegal"]):
        edu = "LLB / LLM (Bachelor / Master of Laws) + Bar Council Enrolment & All India Bar Examination (AIBE)"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹5.0L - ₹9.0L / yr", "₹12.0L - ₹22.0L / yr", "₹30.0L - ₹65.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$70k - $100k / yr", "$140k - $210k / yr", "$250k - $400k / yr"
        roles = [f"Junior Associate Lawyer", f"Senior Associate Advocate", f"Partner / Corporate Counsel", f"Additional District Judge", f"Senior Counsel / Magistrate"]
        sk_b = ["Constitutional & Criminal Law", "Contract & Property Law", "Legal Research & Citation", "Case Brief Writing", "Courtroom Etiquette"]
        sk_i = ["Corporate & Commercial Law", "Civil & Criminal Trial Procedure", "Legal Drafting & Conveyancing", "Intellectual Property Rights", "Arbitration & Mediation"]
        sk_a = ["Appellate Advocacy & Special Leave Petitions", "Cross-Border Mergers & Acquisitions Law", "Regulatory Compliance Architecture", "Constitutional Bench Litigation", "Judicial Decision Making"]
        yt = [{"name": "LegalEagle", "url": "https://www.youtube.com/@LegalEagle"}, {"name": "Bar & Bench Official", "url": "https://www.youtube.com/@barandbench"}, {"name": "LiveLaw India", "url": "https://www.youtube.com/@LiveLawIndia"}, {"name": "Finology Legal", "url": "https://www.youtube.com/@FinologyLegal"}, {"name": "Harvard Law School", "url": "https://www.youtube.com/@harvardlaw"}]
        courses = [{"name": "Coursera Contract Law", "url": "https://www.coursera.org"}, {"name": "edX International Law", "url": "https://www.edx.org"}, {"name": "Swayam Indian Legal System", "url": "https://swayam.gov.in"}, {"name": "NPTEL Legal Studies", "url": "https://nptel.ac.in"}, {"name": "LawSikho Executive Diploma", "url": "https://lawsikho.com"}]
        docs = [{"name": "India Code Portal", "url": "https://www.indiacode.nic.in"}, {"name": "Supreme Court Judgments Portal", "url": "https://main.sci.gov.in"}, {"name": "Law Commission Reports", "url": "https://lawcommissionofindia.nic.in"}, {"name": "Bar Council of India", "url": "http://www.barcouncilofindia.org"}, {"name": "Manupatra Legal Research", "url": "https://www.manupatrafast.in"}]
        books = [{"name": "Introduction to Constitution of India by D.D. Basu", "url": "https://amazon.com"}, {"name": "Law of Contract by Avtar Singh", "url": "https://amazon.com"}, {"name": "Black's Law Dictionary", "url": "https://amazon.com"}, {"name": "Ratanlal & Dhirajlal Indian Penal Code", "url": "https://amazon.com"}, {"name": "Garner's Modern Legal Usage", "url": "https://amazon.com"}]
        projs_b = ["Moot Court Argument Draft", "Basic Commercial Contract Review", "Legal Case Summary Analysis", "Client Interview Consultation Record", "Legal Notice Template Creation"]
        projs_i = ["Corporate NDA & Shareholders Agreement Draft", "Criminal Appeal Case File Preparation", "Pro-Bono Legal Aid Case Brief", "Arbitration Proceedings Strategy Memorandum", "IPR Patent Infringement Audit"]
        projs_a = ["Supreme Court Special Leave Petition Draft", "Cross-Border M&A Legal Due Diligence", "Constitutional Law Amicus Curiae Brief", "Corporate Environmental Compliance Plan", "Judicial Review Commentary"]
        certs = ["All India Bar Examination (AIBE) Certificate", "Certified Corporate Legal Counsel", "Post Graduate Diploma in Cyber Law", "Certified Arbitrator & Mediator", "IPR Specialist Certification"]
        tools = ["SCC Online / Manupatra", "Westlaw / LexisNexis", "Legal Contract Lifecycle Management (CLM)", "e-Courts Filing Portal", "Grammarly Legal Editor"]
        top_orgs = ["Supreme Court of India", "AZB & Partners", "Cyril Amarchand Mangaldas", "Trilegal", "Khaitan & Co"]
        hotspots = [{"city": "New Delhi", "demand": "Very High", "reason": "Supreme Court, Delhi High Court & major law firm HQs."}, {"city": "Mumbai", "demand": "High", "reason": "Financial capital, Bombay High Court & corporate law practices."}, {"city": "London / UK", "demand": "High", "reason": "Global commercial arbitration & International law firms."}, {"city": "New York / USA", "demand": "High", "reason": "Corporate M&A law & Federal Court litigation."}, {"city": "Bengaluru", "demand": "Moderate-High", "reason": "Tech startup legal compliance, IP law & High Court."}]
        trend_skills = ["Tech & AI Legal Compliance", "Cross-Border Arbitration", "Data Privacy & GDPR Law", "IP & Patent Prosecution", "ESG & Environmental Law"]
        daily_plan = ["Monday: 2 hrs Constitutional & Contract Law Study", "Tuesday: 2 hrs Legal Drafting & Case Analysis", "Wednesday: 2 hrs Court Procedure & Precedents Review", "Thursday: 2 hrs Client Consultation & Contract Review", "Friday: 2 hrs Moot Court & Advocacy Practice", "Saturday: 3 hrs Legal Research & Citation Study", "Sunday: 1 hr Weekly Legal Case Digest"]
    elif any(w in c_low for w in ["product manager", "product owner", "pm"]):
        edu = "Bachelor's / Master's Degree in STEM or Business (MBA / B.Tech) + Product Management Portfolio"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹10.0L - ₹16.0L / yr", "₹20.0L - ₹35.0L / yr", "₹38.0L - ₹75.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$95k - $135k / yr", "$150k - $210k / yr", "$220k - $360k / yr"
        roles = ["Associate Product Manager", "Product Manager", "Senior Product Manager", "Group Product Manager", "VP / Chief Product Officer (CPO)"]
        sk_b = ["Product Requirements Document (PRD)", "User Story Mapping", "Wireframing & Prototyping", "A/B Testing Fundamentals", "Product Backlog Grooming"]
        sk_i = ["Product Analytics (Mixpanel/Amplitude)", "RICE / ICE Prioritization Frameworks", "Agile & Scrum Methodologies", "Go-To-Market (GTM) Strategy", "SQL for Product Managers"]
        sk_a = ["Product Portfolio Strategy", "Unit Economics & Monetization", "Executive Stakeholder Alignment", "AI & LLM Product Integration", "Growth Hacking & Retention Loops"]
        yt = [{"name": "Product School", "url": "https://www.youtube.com/@ProductSchool"}, {"name": "Dan Olsen", "url": "https://www.youtube.com/@DanOlsen"}, {"name": "Lenny's Podcast", "url": "https://www.youtube.com/@lennyspodcast"}, {"name": "Harvard Business Review", "url": "https://www.youtube.com/@harvardbusinessreview"}, {"name": "Exponent - PM Interviews", "url": "https://www.youtube.com/@tryexponent"}]
        courses = [{"name": "Coursera Product Management Specialization", "url": "https://www.coursera.org"}, {"name": "Reforge Product Leadership", "url": "https://www.reforge.com"}, {"name": "Pragmatic Institute Certification", "url": "https://www.pragmaticinstitute.com"}, {"name": "Product School Certification", "url": "https://productschool.com"}, {"name": "Udemy PM Bootcamp", "url": "https://www.udemy.com"}]
        docs = [{"name": "Atlassian Agile & Product Guide", "url": "https://www.atlassian.com/agile"}, {"name": "Mixpanel Analytics Documentation", "url": "https://docs.mixpanel.com"}, {"name": "Amplitude Behavioral Analytics Guide", "url": "https://www.amplitude.com"}, {"name": "Product-Led Growth Guide", "url": "https://productled.com"}, {"name": "Silicon Valley Product Group (SVPG)", "url": "https://www.svpg.com"}]
        books = [{"name": "Inspired: How to Create Tech Products Customers Love by Marty Cagan", "url": "https://amazon.com"}, {"name": "Cracking the PM Interview by Gayle Laakmann McDowell", "url": "https://amazon.com"}, {"name": "The Lean Startup by Eric Ries", "url": "https://amazon.com"}, {"name": "Escaping the Build Trap by Melissa Perri", "url": "https://amazon.com"}, {"name": "Product-Led Growth by Wes Bush", "url": "https://amazon.com"}]
        projs_b = ["Product Requirements Document (PRD) for Mobile App", "User Persona & Customer Journey Map", "Competitive Product Feature Audit", "Feature Prioritization Matrix (RICE)", "Basic Wireframe Mockup in Figma"]
        projs_i = ["Mixpanel User Funnel & Retention Analysis", "A/B Test Experimentation Plan & Analysis", "Go-To-Market (GTM) Launch Plan for SaaS", "Product Roadmap & Backlog Sprint Setup", "Customer Churn Reduction Strategy"]
        projs_a = ["AI-Powered Feature Integration Strategy", "Enterprise Platform Monetization Model", "Multi-Product Portfolio Strategy Blueprint", "Global Product Expansion Roadmap", "C-Suite Product Review Deck"]
        certs = ["Certified Scrum Product Owner (CSPO)", "Product School Certified Product Manager (CPM)", "Pragmatic Institute Certified (PMC)", "PMI Agile Certified Practitioner (PMI-ACP)", "Google Project Management Certificate"]
        tools = ["Jira & Confluence", "Figma / Miro Prototyping", "Mixpanel / Amplitude Analytics", "Postman & SQL DB Querying", "Notion & Linear Workspace"]
        top_orgs = ["Google", "Meta", "Microsoft", "Uber", "Airbnb"]
        hotspots = [{"city": "San Francisco / Silicon Valley", "demand": "Very High", "reason": "Global product management headquarters & tech leaders."}, {"city": "Bengaluru / India", "demand": "Very High", "reason": "India's premier product tech hub & unicorn startup ecosystem."}, {"city": "New York", "demand": "High", "reason": "Fintech & consumer media product management."}, {"city": "London / UK", "demand": "High", "reason": "European tech hub & international product teams."}, {"city": "Seattle / Remote", "demand": "High", "reason": "Amazon, Microsoft & cloud product HQs."}]
        trend_skills = ["AI & LLM Product Management", "Product-Led Growth (PLG)", "Data-Driven A/B Testing", "Behavioral Analytics", "Unit Economics & SaaS Metrics"]
        daily_plan = ["Monday: 2 hrs User Research & Customer Feedback Analysis", "Tuesday: 2 hrs PRD Writing & Feature Specification", "Wednesday: 2 hrs Product Analytics & Funnel Review", "Thursday: 2 hrs Cross-Functional Team & Sprint Alignment", "Friday: 2 hrs Product Roadmap & Prioritization Review", "Saturday: 3 hrs Mock PM Interview & Case Study Practice", "Sunday: 1 hr Weekly Product Metrics Audit"]
    elif any(w in c_low for w in ["pilot", "aviator", "flight"]):
        edu = "High School (Physics & Math) + Flight Training Academy + DGCA / FAA Commercial Pilot License (CPL)"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹12.0L - ₹20.0L / yr", "₹28.0L - ₹45.0L / yr", "₹55.0L - ₹1.2Cr / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$85k - $120k / yr", "$160k - $240k / yr", "$280k - $450k / yr"
        roles = ["Junior First Officer", "Senior First Officer", "Airline Captain", "Check Pilot / Flight Instructor", "Chief Pilot / Director of Flight Operations"]
        sk_b = ["Aeronautical Principles & Aerodynamics", "Aviation Meteorology & Weather", "Air Navigation & Flight Planning", "Flight Radio Telephony (RTR)", "Aircraft General Knowledge"]
        sk_i = ["Instrument Flying Protocols (IFR)", "Multi-Engine Aircraft Operations", "Cockpit Resource Management (CRM)", "Flight Simulator Procedures", "Aviation Regulations (ICAO/FAA/DGCA)"]
        sk_a = ["Commercial Airline Type Rating (A320/B737)", "Emergency Emergency Checklist Execution", "Transoceanic Navigation", "Heavy Jet Operations", "Flight Safety & Incident Investigation"]
        yt = [{"name": "Mentour Pilot", "url": "https://www.youtube.com/@MentourPilot"}, {"name": "Captain Joe", "url": "https://www.youtube.com/@CaptainJoe"}, {"name": "Boldmethod", "url": "https://www.youtube.com/@boldmethod"}, {"name": "FlightRadar24", "url": "https://www.youtube.com/@flightradar24"}, {"name": "Flight Level 360", "url": "https://www.youtube.com/@FlightLevel360"}]
        courses = [{"name": "FAA Aviation Ground School", "url": "https://www.faa.gov"}, {"name": "Embry-Riddle Aeronautical Online", "url": "https://erau.edu"}, {"name": "CAE Aviation Training", "url": "https://www.cae.com"}, {"name": "Indira Gandhi Rashtriya Uran Akademi (IGRUA)", "url": "http://igrua.gov.in"}, {"name": "Coursera Aviation Management", "url": "https://www.coursera.org"}]
        docs = [{"name": "ICAO Aviation Safety Standards", "url": "https://www.icao.int"}, {"name": "FAA Pilot Handbooks", "url": "https://www.faa.gov/regulations_policies/handbooks_manuals/aviation"}, {"name": "DGCA India Civil Aviation Requirements", "url": "https://www.dgca.gov.in"}, {"name": "EASA Flight Regulations", "url": "https://www.easa.europa.eu"}, {"name": "Jeppesen Aeronautical Charts", "url": "https://www.jeppesen.com"}]
        books = [{"name": "Stick and Rudder by Wolfgang Langewiesche", "url": "https://amazon.com"}, {"name": "FAA Pilot's Handbook of Aeronautical Knowledge", "url": "https://amazon.com"}, {"name": "Weather Flying by Robert Buck", "url": "https://amazon.com"}, {"name": "FAA Instrument Flying Handbook", "url": "https://amazon.com"}, {"name": "Turbine Pilot's Flight Manual", "url": "https://amazon.com"}]
        projs_b = ["Cross-Country Flight Plan Calculation Log", "Aviation Meteorology Weather Map Analysis", "Aircraft Weight & Balance Sheet", "Air Radio Telephony Procedure Practice", "Flight Simulator Basic Circuit Practice"]
        projs_i = ["Instrument Approach Chart (ILS/VOR) Analysis", "Multi-Engine Emergency Procedures Log", "Cockpit Resource Management Case Review", "Flight Simulator IFR Navigation Procedure", "International Route Planning Study"]
        projs_a = ["Commercial Airline Type Rating (A320/B737) Prep", "Aviation Safety Incident Investigation Report", "Transoceanic ETOPS Flight Planning Model", "Commercial Fleet Operational Audit", "Chief Pilot Flight Safety Review"]
        certs = ["Student Pilot License (SPL)", "Private Pilot License (PPL)", "Commercial Pilot License (CPL)", "Instrument Rating (IR)", "Airline Transport Pilot License (ATPL)"]
        tools = ["ForeFlight EFB App", "Garmin G1000 Glass Cockpit Simulator", "LogTen Pro Digital Flight Logbook", "SkyVector Aeronautical Charts", "Jeppesen FliteDeck"]
        top_orgs = ["IndiGo Airlines", "Air India", "Emirates", "Delta Air Lines", "Boeing / Airbus Flight Flight Training"]
        hotspots = [{"city": "New Delhi / Gurugram", "demand": "Very High", "reason": "IndiGo & Air India headquarters & training simulators."}, {"city": "Dubai / UAE", "demand": "Very High", "reason": "Emirates global international long-haul aviation hub."}, {"city": "Dallas / USA", "demand": "High", "reason": "Major US airline pilot bases & flight academies."}, {"city": "Singapore", "demand": "High", "reason": "Singapore Airlines & Asia-Pacific aviation hub."}, {"city": "Mumbai", "demand": "High", "reason": "Major international airport & commercial flight crews."}]
        trend_skills = ["Glass Cockpit Avionics (G1000)", "Predictive Turbulence Navigation", "Sustainable Aviation Fuel Protocols", "Advanced CRM", "EFB Digital Flight Planning"]
        daily_plan = ["Monday: 2 hrs Aerodynamics & Flight Physics Study", "Tuesday: 2 hrs Navigation & Flight Planning Practice", "Wednesday: 2 hrs Aviation Meteorology & Weather Analysis", "Thursday: 2 hrs Flight Radio Telephony (RTR) Practice", "Friday: 2 hrs Instrument Flight Rules (IFR) Procedure Review", "Saturday: 3 hrs Flight Simulator Practice & Logbook Review", "Sunday: 1 hr Flight Safety & Emergency Protocol Review"]
    elif any(w in c_low for w in ["data scientist", "data science", "machine learning", "ai engineer", "data analyst"]):
        edu = "Bachelor's / Master's Degree in Computer Science, Statistics, Mathematics or Data Science Portfolio"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹8.0L - ₹14.0L / yr", "₹18.0L - ₹32.0L / yr", "₹35.0L - ₹65.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$85k - $125k / yr", "$140k - $195k / yr", "$210k - $340k / yr"
        roles = ["Junior Data Analyst / Data Scientist", "Senior Data Scientist", "Lead AI / ML Engineer", "Principal Data Architect", "Head of Data Science / VP of AI"]
        sk_b = ["Python Programming (Pandas & NumPy)", "SQL & Relational Database Querying", "Exploratory Data Analysis (EDA)", "Applied Probability & Statistics", "Data Visualization (Matplotlib/Seaborn)"]
        sk_i = ["Scikit-Learn & Supervised Machine Learning", "Feature Engineering & Data Cleaning", "Deep Learning (PyTorch / TensorFlow)", "Big Query & Cloud Data Warehousing", "FastAPI / Model Deployment"]
        sk_a = ["Large Language Models (LLMs) & Fine-Tuning", "MLOps & Automated Pipeline Deployment (MLflow)", "Distributed Computing (PySpark)", "Recommendation Systems & Vector DBs", "A/B Testing & Causal Inference"]
        yt = [{"name": "StatQuest with Josh Starmer", "url": "https://www.youtube.com/@statquest"}, {"name": "3Blue1Brown", "url": "https://www.youtube.com/@3blue1brown"}, {"name": "Andrej Karpathy", "url": "https://www.youtube.com/@AndrejKarpathy"}, {"name": "Krish Naik", "url": "https://www.youtube.com/@krishnaik06"}, {"name": "Kaggle Official", "url": "https://www.youtube.com/@Kaggle"}]
        courses = [{"name": "Coursera Deep Learning Specialization by Andrew Ng", "url": "https://www.coursera.org"}, {"name": "Fast.ai Practical Deep Learning for Coders", "url": "https://www.fast.ai"}, {"name": "Udacity Data Scientist Nanodegree", "url": "https://www.udacity.com"}, {"name": "Kaggle Micro-Courses", "url": "https://www.kaggle.com/learn"}, {"name": "edX Professional Certificate in Data Science", "url": "https://www.edx.org"}]
        docs = [{"name": "Scikit-Learn Official User Guide", "url": "https://scikit-learn.org"}, {"name": "PyTorch Documentation & Tutorials", "url": "https://pytorch.org"}, {"name": "Pandas Data Analysis Library Docs", "url": "https://pandas.pydata.org"}, {"name": "TensorFlow Core Guide", "url": "https://www.tensorflow.org"}, {"name": "Hugging Face Transformers Docs", "url": "https://huggingface.co/docs"}]
        books = [{"name": "Designing Data-Intensive Applications by Martin Kleppmann", "url": "https://amazon.com"}, {"name": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow by Aurélien Géron", "url": "https://amazon.com"}, {"name": "Python for Data Analysis by Wes McKinney", "url": "https://amazon.com"}, {"name": "Deep Learning by Ian Goodfellow & Yoshua Bengio", "url": "https://amazon.com"}, {"name": "Pattern Recognition and Machine Learning by Christopher Bishop", "url": "https://amazon.com"}]
        projs_b = ["Exploratory Data Analysis on Real-World Dataset", "Customer Churn Prediction Model using Logistic Regression", "Housing Price Regression Pipeline", "Interactive Streamlit Data Dashboard", "SQL Database Data Cleaning & ETL Script"]
        projs_i = ["Image Classification System with PyTorch CNN", "Sentiment Analysis NLP API with FastAPI", "End-to-End MLOps Pipeline with MLflow & Docker", "Customer Segmentation Clustering Model", "BigQuery Real-Time Analytics Pipeline"]
        projs_a = ["RAG (Retrieval-Augmented Generation) AI Assistant with Vector DB", "Fine-Tuned LLaMA/Mistral Model for Domain Tasks", "Recommendation Engine with Graph Neural Networks", "Real-Time Fraud Detection System on Streaming Data", "Enterprise AI Model Governance & Drift Monitor"]
        certs = ["AWS Certified Machine Learning - Specialty", "TensorFlow Developer Certificate", "Google Professional Machine Learning Engineer", "Databricks Certified Data Scientist", "Microsoft Certified: Azure AI Engineer Associate"]
        tools = ["Python & Jupyter Notebooks", "PyTorch / TensorFlow", "SQL (Snowflake / BigQuery / PostgreSQL)", "Git & Docker", "MLflow & FastAPI"]
        top_orgs = ["Google DeepMind", "OpenAI", "Microsoft AI", "Meta AI Research", "Amazon Web Services"]
        hotspots = [{"city": "San Francisco / Silicon Valley", "demand": "Very High", "reason": "Global AI & LLM research headquarters & top tech companies."}, {"city": "Bengaluru / India", "demand": "Very High", "reason": "India's premier AI/ML engineering hub & R&D centers."}, {"city": "Seattle / Remote", "demand": "High", "reason": "Amazon AI & Microsoft Research headquarters."}, {"city": "London / UK", "demand": "High", "reason": "DeepMind HQs & European AI innovation hubs."}, {"city": "New York", "demand": "High", "reason": "Wall Street quantitative finance & AI analytics."}]
        trend_skills = ["LLM Fine-Tuning & Prompt Engineering", "Vector Databases (Pinecone/Chroma)", "MLOps & Automated Pipelines", "Generative AI Systems", "Causal ML & A/B Testing"]
        daily_plan = ["Monday: 2 hrs Linear Algebra & Statistical Probability", "Tuesday: 2 hrs Python Data Cleaning & Feature Engineering", "Wednesday: 2 hrs ML Model Training & Hyperparameter Tuning", "Thursday: 2 hrs Deep Learning & PyTorch Model Building", "Friday: 2 hrs MLOps Pipeline Deployment & Dockerization", "Saturday: 3 hrs Kaggle Competition & Portfolio Project", "Sunday: 1 hr AI Research Paper Reading"]
    elif any(w in c_low for w in ["software engineer", "developer", "full stack", "backend", "frontend", "coder", "programmer"]):
        edu = "Bachelor's Degree in Computer Science, Software Engineering or Self-Taught Full-Stack Portfolio"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹7.0L - ₹12.0L / yr", "₹16.0L - ₹28.0L / yr", "₹32.0L - ₹55.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$80k - $115k / yr", "$135k - $185k / yr", "$195k - $320k / yr"
        roles = ["Junior Software Engineer", "Software Development Engineer (SDE-2)", "Senior Software Engineer", "Staff / Principal Software Architect", "VP of Engineering / CTO"]
        sk_b = ["Data Structures & Algorithms (DSA)", "Object-Oriented Programming (OOP)", "Git & Version Control", "Relational Databases (PostgreSQL/MySQL)", "HTTP / REST API Fundamentals"]
        sk_i = ["Full-Stack Frameworks (React / Node.js / Python / Java)", "System Design & Microservices Architecture", "Docker Containerization & CI/CD", "NoSQL Databases (MongoDB / Redis)", "Unit Testing & Test-Driven Development (TDD)"]
        sk_a = ["Distributed Systems & High Availability", "Cloud Architecture (AWS / GCP / Azure)", "Kafka Event-Driven Architecture", "Security & OAuth2 / OpenID Authentication", "Performance Profiling & Database Index Tuning"]
        yt = [{"name": "FreeCodeCamp", "url": "https://www.youtube.com/@freecodecamp"}, {"name": "Fireship", "url": "https://www.youtube.com/@Fireship"}, {"name": "Traversy Media", "url": "https://www.youtube.com/@TraversyMedia"}, {"name": "Web Dev Simplified", "url": "https://www.youtube.com/@WebDevSimplified"}, {"name": "NeetCode", "url": "https://www.youtube.com/@NeetCode"}]
        courses = [{"name": "Coursera Computer Science Specialization", "url": "https://www.coursera.org"}, {"name": "Full Stack Open by University of Helsinki", "url": "https://fullstackopen.com"}, {"name": "Udemy Complete Web Development Bootcamp", "url": "https://www.udemy.com"}, {"name": "Frontend Masters Professional Engineering", "url": "https://frontendmasters.com"}, {"name": "edX CS50 Introduction to Computer Science", "url": "https://cs50.harvard.edu"}]
        docs = [{"name": "MDN Web Docs", "url": "https://developer.mozilla.org"}, {"name": "React Official Documentation", "url": "https://react.dev"}, {"name": "Node.js API Reference", "url": "https://nodejs.org/docs"}, {"name": "PostgreSQL Documentation", "url": "https://www.postgresql.org/docs"}, {"name": "Docker Official Guide", "url": "https://docs.docker.com"}]
        books = [{"name": "Clean Code: A Handbook of Agile Software Craftsmanship by Robert C. Martin", "url": "https://amazon.com"}, {"name": "System Design Interview by Alex Xu", "url": "https://amazon.com"}, {"name": "Designing Data-Intensive Applications by Martin Kleppmann", "url": "https://amazon.com"}, {"name": "The Pragmatic Programmer by Andrew Hunt", "url": "https://amazon.com"}, {"name": "Cracking the Coding Interview by Gayle Laakmann McDowell", "url": "https://amazon.com"}]
        projs_b = ["Full-Stack Task Manager App with Auth & Database", "RESTful API Backend with PostgreSQL", "Responsive E-Commerce Product Catalog", "Weather Forecast Web App with External API", "CLI Developer Utility Tool"]
        projs_i = ["Real-Time Chat Application with WebSockets", "Microservices Architecture E-Commerce System", "Dockerized CI/CD Deployment Pipeline on AWS", "Distributed Caching Engine with Redis", "OAuth2 Authentication & User Management Microservice"]
        projs_a = ["High-Throughput Distributed Message Queue Engine", "Cloud-Native Serverless Application Architecture", "Low-Latency Video Streaming Platform", "Distributed Database Sharding Manager", "Enterprise API Gateway & Rate Limiter"]
        certs = ["AWS Certified Developer - Associate", "Certified Kubernetes Application Developer (CKAD)", "Meta Front-End / Back-End Developer Professional Cert", "Oracle Certified Professional Java SE", "Google Associate Cloud Engineer"]
        tools = ["VS Code / JetBrains IDEs", "Git & GitHub", "Docker & Kubernetes", "Postman / Insomnia", "PostgreSQL & Redis"]
        top_orgs = ["Google", "Microsoft", "Amazon", "Apple", "Meta"]
        hotspots = [{"city": "San Francisco / Silicon Valley", "demand": "Very High", "reason": "Global software engineering capital."}, {"city": "Bengaluru / India", "demand": "Very High", "reason": "India's premier tech hub & software development centers."}, {"city": "Seattle / USA", "demand": "High", "reason": "Amazon, Microsoft & cloud engineering HQs."}, {"city": "Hyderabad / India", "demand": "High", "reason": "Major global software R&D centers."}, {"city": "London / UK", "demand": "High", "reason": "European technology capital & fintech startups."}]
        trend_skills = ["Microservices & System Design", "Docker & Kubernetes Containerization", "AWS & Cloud-Native Development", "TypeScript & React / Next.js", "AI Code Assistants (Copilot)"]
        daily_plan = ["Monday: 2 hrs Data Structures & Algorithms Practice (LeetCode)", "Tuesday: 2 hrs Backend API Development & Database Schema", "Wednesday: 2 hrs Frontend UI Component Building", "Thursday: 2 hrs Docker Containerization & System Integration", "Friday: 2 hrs Unit Testing & Code Refactoring", "Saturday: 3 hrs Full-Stack Project Building", "Sunday: 1 hr System Design Architecture Study"]
    elif any(w in c_low for w in ["cyber", "security", "ethical hack", "soc", "pentest"]):
        edu = "Bachelor's Degree in Computer Science, Cyber Security, or CEH / CompTIA Security+ Credentials"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹7.5L - ₹12.0L / yr", "₹16.0L - ₹28.0L / yr", "₹30.0L - ₹58.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$80k - $115k / yr", "$130k - $180k / yr", "$190k - $300k / yr"
        roles = ["SOC Analyst L1", "Cybersecurity Specialist", "Senior Ethical Hacker / Penetration Tester", "Lead Incident Response Analyst", "Chief Information Security Officer (CISO)"]
        sk_b = ["Network Fundamentals & TCP/IP Protocols", "Linux & Windows Systems Security", "Wireshark Packet Analysis", "Vulnerability Assessment (Nessus)", "Basic Cryptography & SSL/TLS"]
        sk_i = ["Penetration Testing (Metasploit / Burp Suite)", "SIEM Log Analysis (Splunk / Elastic SOC)", "Incident Response & Forensics", "Web Application Security (OWASP Top 10)", "Cloud Security (AWS IAM & GuardDuty)"]
        sk_a = ["Zero Trust Architecture", "Red Teaming & Adversary Simulation", "Malware Reverse Engineering", "Enterprise Security Compliance (ISO 27001 / SOC 2)", "Security Architecture Blueprinting"]
        yt = [{"name": "NetworkChuck", "url": "https://www.youtube.com/@NetworkChuck"}, {"name": "David Bombal", "url": "https://www.youtube.com/@DavidBombal"}, {"name": "The Cyber Mentor", "url": "https://www.youtube.com/@TheCyberMentor"}, {"name": "John Hammond", "url": "https://www.youtube.com/@JohnHammond"}, {"name": "LiveOverflow", "url": "https://www.youtube.com/@LiveOverflow"}]
        courses = [{"name": "TryHackMe Cyber Security Learning Paths", "url": "https://tryhackme.com"}, {"name": "Hack The Box Academy", "url": "https://academy.hackthebox.com"}, {"name": "Coursera Google Cybersecurity Professional Cert", "url": "https://www.coursera.org"}, {"name": "SANS GIAC Security Training", "url": "https://www.sans.org"}, {"name": "CompTIA Security+ Sybex Certification Prep", "url": "https://www.comptia.org"}]
        docs = [{"name": "OWASP Top 10 Security Risks", "url": "https://owasp.org"}, {"name": "NIST Cybersecurity Framework (CSF)", "url": "https://www.nist.gov/cyberframework"}, {"name": "MITRE ATT&CK Framework Portal", "url": "https://attack.mitre.org"}, {"name": "SANS Security Incident Response Guides", "url": "https://www.sans.org"}, {"name": "CISA Cybersecurity Advisories", "url": "https://www.cisa.gov"}]
        books = [{"name": "The Web Application Hacker's Handbook by Dafydd Stuttard", "url": "https://amazon.com"}, {"name": "Practical Malware Analysis by Michael Sikorski", "url": "https://amazon.com"}, {"name": "CompTIA Security+ Get Certified Get Ahead by Darril Gibson", "url": "https://amazon.com"}, {"name": "Applied Cryptography by Bruce Schneier", "url": "https://amazon.com"}, {"name": "Blue Team Handbook: Incident Response Edition", "url": "https://amazon.com"}]
        projs_b = ["Home Lab Security Network Setup", "Wireshark Network Traffic Analysis Log", "OWASP Top 10 Vulnerability Audit Report", "Linux Server Hardening Script", "Phishing Attack Simulation Report"]
        projs_i = ["TryHackMe CTF Challenge Portfolio", "Web Application Penetration Test Report", "Splunk SIEM Alert & Incident Response Dashboard", "AWS Cloud IAM Security Assessment", "Python Port Scanner & Exploit Script"]
        projs_a = ["Active Directory Enterprise Red Team Assessment", "Malware Sandbox Reverse Engineering Analysis", "Zero Trust Network Migration Plan", "ISO 27001 Security Audit Architecture", "Automated Threat Intelligence Feed"]
        certs = ["CompTIA Security+", "Certified Ethical Hacker (CEH)", "Offensive Security Certified Professional (OSCP)", "Certified Information Systems Security Professional (CISSP)", "GIAC Penetration Tester (GPEN)"]
        tools = ["Wireshark & Nmap", "Burp Suite Pro / Metasploit", "Splunk SIEM / Elastic Security", "Kali Linux & Parrot OS", "Nessus Vulnerability Scanner"]
        top_orgs = ["Palo Alto Networks", "CrowdStrike", "Cloudflare", "Mandiant / Google Cloud", "Cisco Systems"]
        hotspots = [{"city": "Washington D.C. / USA", "demand": "Very High", "reason": "US federal defense, government agencies & cybersecurity HQs."}, {"city": "Bengaluru / India", "demand": "Very High", "reason": "India's premier cybersecurity operations & SOC hubs."}, {"city": "Tel Aviv / Israel", "demand": "Very High", "reason": "Global cyber technology innovation & security startups."}, {"city": "London / UK", "demand": "High", "reason": "European financial cybersecurity & threat intel centers."}, {"city": "Singapore", "demand": "High", "reason": "Asia-Pacific financial security & government cyber agencies."}]
        trend_skills = ["Zero Trust Architecture", "Cloud Security Posture Management (CSPM)", "AI-Powered Threat Detection", "SOAR Automation", "Identity & Access Management (IAM)"]
        daily_plan = ["Monday: 2 hrs TCP/IP & Network Protocol Analysis", "Tuesday: 2 hrs Linux Hardening & Command Line Practice", "Wednesday: 2 hrs Wireshark & Packet Capture Analysis", "Thursday: 2 hrs Burp Suite Web Application Security Practice", "Friday: 2 hrs TryHackMe / HackTheBox Machine Solving", "Saturday: 3 hrs Capture The Flag (CTF) Practice", "Sunday: 1 hr Threat Intel & Vulnerability Advisory Reading"]
    elif any(w in c_low for w in ["ui", "ux", "graphic", "designer", "illustrator", "animator", "creative director"]):
        edu = "Bachelor's Degree in Graphic Design, Interaction Design, Fine Arts or Self-Taught Figma Portfolio"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹5.5L - ₹9.5L / yr", "₹14.0L - ₹24.0L / yr", "₹28.0L - ₹50.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$65k - $95k / yr", "$105k - $150k / yr", "$160k - $250k / yr"
        roles = ["Junior UI/UX Designer", "Product Designer", "Senior UI/UX Specialist", "Lead Design Systems Architect", "Head of Design / Creative Director"]
        sk_b = ["Design Fundamentals & Visual Hierarchy", "Color Theory & Typography", "Figma / Adobe XD Basics", "Wireframing & Low-Fidelity Prototyping", "User Personas & Empathy Mapping"]
        sk_i = ["High-Fidelity Interactive Prototyping", "Design System Creation & Component Tokens", "Usability Testing & User Research", "Responsive Mobile & Web UI Design", "Micro-Interactions & Animation (Lottie/Framer)"]
        sk_a = ["Design Strategy & Product Vision", "Accessibility Standards (WCAG 2.1)", "Design Ops & Developer Handoff", "Information Architecture Blueprinting", "Quantitative UX Research & Analytics"]
        yt = [{"name": "AJ&Smart", "url": "https://www.youtube.com/@AJSmart"}, {"name": "The Futur", "url": "https://www.youtube.com/@TheFutur"}, {"name": "Figma Official Channel", "url": "https://www.youtube.com/@Figma"}, {"name": "DesignCourse", "url": "https://www.youtube.com/@DesignCourse"}, {"name": "Flux Academy", "url": "https://www.youtube.com/@FluxAcademy"}]
        courses = [{"name": "Google UX Design Professional Certificate on Coursera", "url": "https://www.coursera.org"}, {"name": "Interaction Design Foundation (IxDF)", "url": "https://www.interaction-design.org"}, {"name": "Framer University", "url": "https://www.framer.university"}, {"name": "Udemy UI/UX Design Masterclass", "url": "https://www.udemy.com"}, {"name": "Designlab UX Academy", "url": "https://designlab.com"}]
        docs = [{"name": "Figma Design Systems & Token Guide", "url": "https://help.figma.com"}, {"name": "Google Material Design 3 Guidelines", "url": "https://m3.material.io"}, {"name": "Apple Human Interface Guidelines (HIG)", "url": "https://developer.apple.com/design/human-interface-guidelines"}, {"name": "Nielsen Norman Group UX Articles", "url": "https://www.nngroup.com"}, {"name": "WCAG Accessibility Guidelines", "url": "https://www.w3.org/WAI/standards-guidelines/wcag"}]
        books = [{"name": "The Design of Everyday Things by Don Norman", "url": "https://amazon.com"}, {"name": "Don't Make Me Think by Steve Krug", "url": "https://amazon.com"}, {"name": "Refactoring UI by Adam Wathan & Steve Schoger", "url": "https://amazon.com"}, {"name": "Sprint by Jake Knapp", "url": "https://amazon.com"}, {"name": "Laws of UX by Jon Yablonski", "url": "https://amazon.com"}]
        projs_b = ["Mobile E-Commerce App Wireframe & Flow", "Personal Portfolio Website UI Mockup", "Redesign of Local Business Landing Page", "Iconography & Brand Identity Package", "Usability Audit Report of Existing App"]
        projs_i = ["Interactive SaaS Dashboard with Figma Design System", "User Research & Usability Testing Study", "Framer / Webflow Live Interactive Portfolio", "Accessibility (WCAG 2.1) Audit & Redesign", "Mobile Banking App UI/UX Redesign Case Study"]
        projs_a = ["Enterprise Design System Token Library", "Cross-Platform Multi-Brand Design Architecture", "Design Sprint Facilitation & Product Blueprint", "AI-Powered Product Interface Case Study", "Global Brand Strategy & Design Playbook"]
        certs = ["Google UX Design Professional Certificate", "Interaction Design Foundation (IxDF) Certificate", "Certified Figma Professional", "Nielsen Norman Group UX Master Cert", "Certified Usability Analyst (CUA)"]
        tools = ["Figma & FigJam", "Adobe Creative Cloud (Photoshop/Illustrator)", "Framer / Webflow", "Miro & Notion", "Lottie / Principle"]
        top_orgs = ["Apple", "Airbnb", "Figma", "Canva", "IDE0"]
        hotspots = [{"city": "San Francisco / Silicon Valley", "demand": "Very High", "reason": "Global product design, tech startups & Figma HQs."}, {"city": "Bengaluru / India", "demand": "Very High", "reason": "India's premier digital product & UX design ecosystem."}, {"city": "London / UK", "demand": "High", "reason": "Global creative agencies & brand design studios."}, {"city": "Berlin / Germany", "demand": "High", "reason": "European creative tech & UI/UX startup capital."}, {"city": "New York", "demand": "High", "reason": "Media, advertising agencies & digital brand studios."}]
        trend_skills = ["Design System Tokens", "AI-Assisted UI Generation", "Framer Interactive Prototyping", "Accessibility (WCAG)", "Micro-Animations & Lottie"]
        daily_plan = ["Monday: 2 hrs Visual Hierarchy & Typography Study", "Tuesday: 2 hrs User Research & Persona Mapping", "Wednesday: 2 hrs Figma Component & Auto-Layout Building", "Thursday: 2 hrs High-Fidelity Interactive Prototyping", "Friday: 2 hrs Usability Testing & Feedback Iteration", "Saturday: 3 hrs Case Study Writing & Portfolio Building", "Sunday: 1 hr Design Trends & Dribbble / Behance Inspection"]
    elif any(w in c_low for w in ["finance", "financial", "bank", "accountant", "chartered", "ca", "cpa", "cfa", "investment", "auditor", "tax"]):
        edu = "Bachelor's / Master's in Finance, Commerce, Accounting (B.Com/MBA) or CA / CPA / CFA Qualification"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.5L - ₹11.0L / yr", "₹15.0L - ₹26.0L / yr", "₹32.0L - ₹65.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$75k - $110k / yr", "$130k - $190k / yr", "$210k - $380k / yr"
        roles = ["Junior Financial Analyst / Accountant", "Senior Financial Analyst / Auditor", "Investment Banking Associate / Finance Manager", "Vice President of Finance / Director", "Chief Financial Officer (CFO)"]
        sk_b = ["Financial Accounting Principles", "Excel Advanced Functions & Pivot Tables", "Financial Statement Analysis (P&L, Balance Sheet, Cash Flow)", "Corporate Taxation & Compliance", "Double-Entry Bookkeeping"]
        sk_i = ["Financial Modeling & Valuation (DCF / Comps)", "Corporate Finance & Capital Budgeting", "Auditing & Internal Controls", "SAP / Tally ERP Financial Accounting", "Budgeting & Variance Analysis"]
        sk_a = ["Mergers & Acquisitions (M&A) Structuring", "Portfolio Management & Quantitative Analysis", "Regulatory Risk & Compliance (SEC / SEBI)", "Treasury & FX Risk Hedging", "Strategic CFO Decision Making"]
        yt = [{"name": "Aswath Damodaran (NYU Stern)", "url": "https://www.youtube.com/@AswathDamodaranNYU"}, {"name": "Wall Street Prep", "url": "https://www.youtube.com/@WallStreetPrep"}, {"name": "CFA Institute", "url": "https://www.youtube.com/@CFAInstitute"}, {"name": "CA Rachana Ranade", "url": "https://www.youtube.com/@RachanaRanade"}, {"name": "The Valuation School", "url": "https://www.youtube.com/@TheValuationSchool"}]
        courses = [{"name": "CFA Program Candidate Prep", "url": "https://www.cfainstitute.org"}, {"name": "Wall Street Prep Financial Modeling Course", "url": "https://www.wallstreetprep.com"}, {"name": "Coursera Corporate Finance Specialization by Wharton", "url": "https://www.coursera.org"}, {"name": "ICAI Chartered Accountancy Course", "url": "https://www.icai.org"}, {"name": "edX Professional Certificate in Finance", "url": "https://www.edx.org"}]
        docs = [{"name": "IFRS International Financial Reporting Standards", "url": "https://www.ifrs.org"}, {"name": "US GAAP Accounting Standards Board", "url": "https://www.fasb.org"}, {"name": "SEC EDGAR Company Filings Database", "url": "https://www.sec.gov/edgar"}, {"name": "SEBI Regulatory Portal India", "url": "https://www.sebi.gov.in"}, {"name": "Reserve Bank of India (RBI) Notifications", "url": "https://www.rbi.org.in"}]
        books = [{"name": "Valuation: Measuring and Managing the Value of Companies by McKinsey", "url": "https://amazon.com"}, {"name": "The Intelligent Investor by Benjamin Graham", "url": "https://amazon.com"}, {"name": "Corporate Finance by Berk & DeMarzo", "url": "https://amazon.com"}, {"name": "Financial Shenanigans by Howard Schilit", "url": "https://amazon.com"}, {"name": "Financial Modeling by Simon Benninga", "url": "https://amazon.com"}]
        projs_b = ["Three-Statement Financial Model in Excel", "Public Company 10-K Filing Financial Analysis", "Personal Budget & Investment Portfolio Model", "Corporate Working Capital Audit", "Basic Taxation Return Calculation Sheet"]
        projs_i = ["Discounted Cash Flow (DCF) Valuation Model", "Merger & Acquisition (M&A) LBO Model", "Corporate Annual Budget & Variance Analysis Report", "Company Credit Rating & Debt Capacity Study", "SAP ERP Financial Ledger Audit"]
        projs_a = ["Cross-Border M&A Valuation & Due Diligence", "Enterprise Risk Management & Hedging Strategy", "Quantitative Asset Allocation & Backtesting Model", "CFO Strategic Capital Allocation Masterplan", "Global Tax Structuring Memorandum"]
        certs = ["Chartered Financial Analyst (CFA)", "Chartered Accountant (CA) / CPA", "Financial Risk Manager (FRM)", "Financial Modeling & Valuation Analyst (FMVA)", "Certified Management Accountant (CMA)"]
        tools = ["Microsoft Excel & Power BI", "Bloomberg Terminal / Refinitiv Eikon", "SAP Financial Accounting (FI/CO) / Tally", "QuickBooks / Xero", "Capital IQ / PitchBook"]
        top_orgs = ["Goldman Sachs", "JPMorgan Chase", "Morgan Stanley", "Deloitte / PwC / EY / KPMG", "BlackRock"]
        hotspots = [{"city": "New York (Wall Street)", "demand": "Very High", "reason": "Global financial capital, stock exchanges & investment banks."}, {"city": "Mumbai", "demand": "Very High", "reason": "Financial capital of India, RBI, BSE, NSE & corporate HQs."}, {"city": "London / UK", "demand": "Very High", "reason": "European financial capital & global investment banking."}, {"city": "Singapore", "demand": "High", "reason": "Asia-Pacific wealth management & private equity hub."}, {"city": "Hong Kong", "demand": "High", "reason": "Asian capital markets & cross-border finance."}]
        trend_skills = ["Financial Modeling (DCF/LBO)", "Fintech & Algorithmic Trading", "ESG Financial Audit", "Power BI Data Analytics", "Automated Financial Reporting"]
        daily_plan = ["Monday: 2 hrs Financial Accounting & Statement Analysis", "Tuesday: 2 hrs Advanced Excel & Financial Modeling Practice", "Wednesday: 2 hrs Corporate Valuation & DCF Model Building", "Thursday: 2 hrs Corporate Tax & Regulatory Compliance Review", "Friday: 2 hrs Financial Market News & Earnings Report Review", "Saturday: 3 hrs Complex Valuation Project Building", "Sunday: 1 hr Financial Journal Reading & Model Audit"]
    elif any(w in c_low for w in ["chef", "culinary", "cook", "baker", "hotel", "hospitality", "restaurant"]):
        edu = "Diploma / Degree in Culinary Arts, Hotel Management or Apprenticeship in Commercial Kitchens"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹4.0L - ₹7.0L / yr", "₹9.0L - ₹16.0L / yr", "₹20.0L - ₹45.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$45k - $65k / yr", "$75k - $110k / yr", "$120k - $220k / yr"
        roles = ["Commis Chef / Line Cook", "Chef de Partie (Station Chef)", "Sous Chef", "Executive Chef", "Culinary Director / Restaurant Owner"]
        sk_b = ["Professional Knife Skills & Cuts", "Food Safety & HACCP Hygiene Protocols", "Basic Sauce Preparation (5 Mother Sauces)", "Kitchen Station Management", "Food Preparation & Mise en Place"]
        sk_i = ["Advanced Cooking Methods (Sous-Vide/Confit)", "Menu Planning & Food Costing", "Pastry & Baking Techniques", "Inventory & Waste Management", "Commercial Kitchen Team Leadership"]
        sk_a = ["Michelin-Level Culinary Innovation", "Multi-Unit Restaurant Operation", "Kitchen Financial Auditing & P&L", "Global Gastronomy & Flavor Pairing", "Executive Culinary Directorship"]
        yt = [{"name": "Gordon Ramsay", "url": "https://www.youtube.com/@gordonramsay"}, {"name": "Babish Culinary Universe", "url": "https://www.youtube.com/@babishculinaryuniverse"}, {"name": "Eater Official", "url": "https://www.youtube.com/@Eater"}, {"name": "French Cooking Academy", "url": "https://www.youtube.com/@FrenchCookingAcademy"}, {"name": "Pro Home Cooks", "url": "https://www.youtube.com/@ProHomeCooks"}]
        courses = [{"name": "Le Cordon Bleu Culinary Programs", "url": "https://www.cordonbleu.edu"}, {"name": "Culinary Institute of America (CIA) Online", "url": "https://www.ciachef.edu"}, {"name": "Rouxbe Online Culinary School", "url": "https://rouxbe.com"}, {"name": "Coursera Food Safety & Hospitality", "url": "https://www.coursera.org"}, {"name": "IHM India Hotel Management Course", "url": "http://nchm.nic.in"}]
        docs = [{"name": "FSSAI Food Safety Standards India", "url": "https://www.fssai.gov.in"}, {"name": "FDA Food Code Manual", "url": "https://www.fda.gov/food/fda-food-code"}, {"name": "HACCP Food Safety Principles", "url": "https://www.haccpalliance.org"}, {"name": "ServSafe Manager Guidelines", "url": "https://www.servsafe.com"}, {"name": "World Chefs Standards", "url": "https://worldchefs.org"}]
        books = [{"name": "The Professional Chef by The Culinary Institute of America", "url": "https://amazon.com"}, {"name": "Salt, Fat, Acid, Heat by Samin Nosrat", "url": "https://amazon.com"}, {"name": "On Food and Cooking by Harold McGee", "url": "https://amazon.com"}, {"name": "The Flavor Bible by Karen Page & Andrew Dornenburg", "url": "https://amazon.com"}, {"name": "Kitchen Confidential by Anthony Bourdain", "url": "https://amazon.com"}]
        projs_b = ["Commercial Kitchen Knife Precision Portfolio", "Five Mother Sauces Preparation Guide", "HACCP Food Safety Audit Log", "Basic Recipe Costing Spreadsheet", "Kitchen Station Sanitation Plan"]
        projs_i = ["Seasonal Restaurant Menu Design & Costing", "Sous-Vide & Precision Temperature Cooking Portfolio", "Commercial Kitchen Layout & Equipment Plan", "Food Waste Reduction & Sustainability Plan", "Multi-Course Banquet Event Planning Deck"]
        projs_a = ["Fine-Dining Tasting Menu & Pairing Portfolio", "Multi-Unit Restaurant Culinary P&L Model", "Executive Chef Operational Playbook", "Global Gastronomy Recipe Publication", "Culinary Brand Launch Strategy"]
        certs = ["ServSafe Food Protection Manager", "Certified Executive Chef (CEC)", "HACCP Food Safety Certification", "WSET Wine & Beverage Qualification", "Le Cordon Bleu Culinary Diploma"]
        tools = ["Professional Chef Knife Set (Shun/Wüsthof)", "Sous-Vide Precision Cooker & Chamber Sealer", "ServSafe Food Thermometer", "Commercial Combination Oven", "Restaurant POS & Inventory Software (Toast/Lightspeed)"]
        top_orgs = ["Marriott International", "Taj Hotels (IHCL)", "The Ritz-Carlton", "Hilton Hotels", "Michelin-Starred Restaurant Groups"]
        hotspots = [{"city": "Paris / France", "demand": "Very High", "reason": "Global gastronomy capital & classical culinary heritage."}, {"city": "New York", "demand": "Very High", "reason": "Diverse world-class dining & Michelin-starred restaurants."}, {"city": "Mumbai / Goa", "demand": "High", "reason": "Premier luxury hotel chains & booming fine dining industry."}, {"city": "Tokyo / Japan", "demand": "Very High", "reason": "Highest density of Michelin stars & culinary precision."}, {"city": "Dubai / UAE", "demand": "High", "reason": "Luxury hospitality & international celebrity chef outlets."}]
        trend_skills = ["Molecular Gastronomy & Sous-Vide", "Plant-Based Culinary Innovation", "Food Costing & Waste Reduction", "HACCP Digital Safety Management", "Flavor Pairing Science"]
        daily_plan = ["Monday: 2 hrs Knife Technique & Speed Practice", "Tuesday: 2 hrs Sauce Preparation & Flavor Profiling", "Wednesday: 2 hrs Recipe Development & Food Costing", "Thursday: 2 hrs HACCP Sanitation & Kitchen Operations Audit", "Friday: 2 hrs Line Cooking Simulation & Plating", "Saturday: 3 hrs Banquet Event Cooking & Menu Execution", "Sunday: 1 hr Culinary Book Reading & Recipe Logging"]
    elif any(w in c_low for w in ["farmer", "agronomist", "botanist", "agriculture", "crop"]):
        edu = "B.Sc / M.Sc in Agricultural Science, Agronomy, Horticulture or Hands-On Farming Practice"
        sal_ind_f, sal_ind_m, sal_ind_s = "₹3.5L - ₹6.5L / yr", "₹8.0L - ₹14.0L / yr", "₹18.0L - ₹32.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$45k - $65k / yr", "$80k - $120k / yr", "$140k - $220k / yr"
        roles = [f"Assistant Agronomist", f"Farm Operations Manager", f"Senior Agricultural Specialist", f"Agri-Business Director", f"Principal Soil & Crop Consultant"]
        sk_b = ["Soil Chemistry & Fertility", "Crop Rotation & Seasons", "Basic Irrigation Techniques", "Organic Farming Principles", "Farm Machinery Operation"]
        sk_i = ["Precision Agriculture & Drones", "Pest & Weed Management", "Agri-Market Pricing & Economics", "Hydroponics & Greenhouse Tech", "Water Conservation & Harvesting"]
        sk_a = ["Climate-Resilient Crop Breeding", "Large-Scale Agri-Supply Chain Tech", "Soil Microbiome Restoration", "Agricultural Export Compliance", "Agri-Fintech & Futures Trading"]
        yt = [{"name": "Krishi Darshan Official", "url": "https://www.youtube.com/@DoordarshanKisan"}, {"name": "Farming Leader", "url": "https://www.youtube.com/@FarmingLeader"}, {"name": "Discover Agriculture", "url": "https://www.youtube.com/@DiscoverAgriculture"}, {"name": "Cornell Small Farms", "url": "https://www.youtube.com/@CornellSmallFarms"}, {"name": "Agronomy TV", "url": "https://www.youtube.com/@AgronomyTV"}]
        courses = [{"name": "NPTEL Agriculture & Food Engineering", "url": "https://nptel.ac.in/courses/126"}, {"name": "Swayam Organic Farming Course", "url": "https://onlinecourses.swayam2.ac.in/arp19_ap75/preview"}, {"name": "Coursera Sustainable Agricultural Land Management", "url": "https://www.coursera.org/learn/sustainable-agricultural-land-management"}, {"name": "edX Sustainable Food Systems", "url": "https://www.edx.org/learn/food-production/wageningen-university-research-sustainable-food-systems-a-systemic-approach"}, {"name": "Wageningen University Agriculture & Environment", "url": "https://www.wur.nl/en/Education-Programmes.htm"}]
        docs = [{"name": "ICAR Research Guidelines & Standards", "url": "https://icar.org.in/content/icar-guidelines"}, {"name": "Agmarknet Daily Commodity Price Portal", "url": "https://agmarknet.gov.in/SearchPage/SearchAndDetails.aspx"}, {"name": "FAO Agriculture Standards & Policies", "url": "https://www.fao.org/standards/en"}, {"name": "Ministry of Agriculture India Official Portal", "url": "https://agricoop.nic.in/en/major-initiatives"}, {"name": "Kisan Call Centre Directory & Portal", "url": "https://dge.gov.in/dge/kisan_call_centre"}]
        books = [{"name": "Principles of Agronomy by Yellamanda Reddy", "url": "https://www.amazon.in/Principles-Agronomy-S-Reddy-Reddy/dp/8177545731"}, {"name": "Introductory Soil Science by D.K. Das", "url": "https://www.amazon.in/Introductory-Soil-Science-D-Das/dp/9381450259"}, {"name": "Plant Breeding Principles by B.D. Singh", "url": "https://www.amazon.in/Plant-Breeding-Principles-B-Singh/dp/8127267151"}, {"name": "Agricultural Economics by Subba Reddy", "url": "https://www.amazon.in/Agricultural-Economics-S-Subba-Reddy/dp/8120417379"}, {"name": "The One-Straw Revolution by Masanobu Fukuoka", "url": "https://www.amazon.com/One-Straw-Revolution-Introduction-Natural-Farming/dp/1590173139"}]
        projs_b = ["Soil pH & Nutrient Testing Report", "Seasonal Crop Rotation Plan", "Basic Drip Irrigation Blueprint", "Organic Compost Preparation Study", "Farm Tool Maintenance Logbook"]
        projs_i = ["Drone-Based Crop Health Survey", "Hydroponic Vertical Farm Setup", "Integrated Pest Management Plan", "Farm-to-Market Supply Chain Model", "Water Harvesting Reservoir Design"]
        projs_a = ["Climate-Resilient Smart Agriculture Plan", "State-Level Agri-Cooperative Business Plan", "Biological Soil Restoration Trial", "Organic Export Compliance Portfolio", "Agri-Tech IoT Sensor Network"]
        certs = ["Certified Organic Farming Specialist", "Agricultural Drone Pilot License", "Soil Testing & Nutrient Management Cert", "Good Agricultural Practices (GAP) Cert", "Certified Crop Adviser (CCA)"]
        tools = ["Agricultural Drones & Multispectral Cameras", "Smart Drip Irrigation Telemetry", "Soil pH & NPK Testers", "Kisan Suvidha & Agmarknet Apps", "Tractor & Precision Seeder Tech"]
        top_orgs = ["ICAR (Indian Council of Agricultural Research)", "NABARD", "Mahindra Agri Business", "Syngenta India", "John Deere"]
        hotspots = [{"city": "Punjab & Haryana", "demand": "Very High", "reason": "Leading agricultural belt with high mechanized farming."}, {"city": "Wageningen / Netherlands", "demand": "Very High", "reason": "Global capital for high-tech greenhouse & agritech innovation."}, {"city": "Iowa / USA", "demand": "High", "reason": "Major corn & soybean precision agriculture hub."}, {"city": "Maharashtra", "demand": "High", "reason": "Pioneer in commercial horticulture & sugarcane farming."}, {"city": "Andhra Pradesh", "demand": "High", "reason": "Natural farming & aqua-agri export centers."}]
        trend_skills = ["Precision Drones & Satellite Mapping", "Hydroponics & Aeroponics", "Soil Microbiome Tech", "Agri-Market Analytics", "Climate-Resilient Farming"]
        daily_plan = ["Monday: 2 hrs Soil Science & Nutrient Management", "Tuesday: 2 hrs Crop Pest & Disease Diagnosis", "Wednesday: 2 hrs Precision Irrigation & Drone Mapping", "Thursday: 2 hrs Agri-Market Price & Economics Study", "Friday: 2 hrs Practical Field Demonstration & Work", "Saturday: 3 hrs Farm Tool Maintenance & Field Survey", "Sunday: 1 hr Weekly Crop Growth Review"]
    else:
        # General Professional & Specialized Careers
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.5L - ₹10.0L / yr", "₹14.0L - ₹22.0L / yr", "₹25.0L - ₹48.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$70k - $95k / yr", "$120k - $160k / yr", "$180k - $270k / yr"
        edu = f"Degree / Diploma in {c_title} or related field + Industry Certification & Professional Portfolio"
        roles = [f"Assistant {c_title}", f"Associate {c_title}", f"Senior {c_title} Lead", f"Principal {c_title} Specialist", f"Director of {c_title}"]
        sk_b = ["Domain Foundational Principles", "Standard Operating Procedures (SOPs)", "Industry Analytical Tools", "Core Workflow Optimization", "Professional Communication"]
        sk_i = ["Advanced Execution Methodologies", "Quality Assurance & Compliance", "Data-Driven Performance Tracking", "Project Lifecycle Management", "Cross-Functional Coordination"]
        sk_a = ["Strategic Leadership & Governance", "Enterprise Operations Scaling", "Risk Mitigation & Auditing", "Resource & Capital Allocation", "Executive Decision Making"]
        yt = [{"name": "TED Talks & Professional Growth", "url": "https://www.youtube.com/@TED"}, {"name": "CrashCourse Professional Track", "url": "https://www.youtube.com/@crashcourse"}, {"name": "Harvard Business Review Channel", "url": "https://www.youtube.com/@harvardbusinessreview"}, {"name": "MIT OpenCourseWare Lectures", "url": "https://www.youtube.com/@mitocw"}, {"name": "LinkedIn Learning Insights", "url": "https://www.youtube.com/@linkedinlearning"}]
        courses = [{"name": "Google Project Management Certificate on Coursera", "url": "https://www.coursera.org/professional-certificates/google-project-management"}, {"name": "Harvard Business Principles on edX", "url": "https://www.edx.org/learn/business-administration/harvard-university-exercising-leadership-foundational-principles"}, {"name": "Udemy Management & Leadership Masterclass", "url": "https://www.udemy.com/course/management-leadership-masterclass/"}, {"name": "LinkedIn Learning Leadership Foundations", "url": "https://www.linkedin.com/learning/leadership-foundations-2"}, {"name": "Jira Fundamentals Course on Atlassian University", "url": "https://university.atlassian.com/student/path/905295-jira-fundamentals"}]
        docs = [{"name": "ISO 9001 Quality Management Standard Guidelines", "url": "https://www.iso.org/iso-9001-quality-management.html"}, {"name": "NIST Professional Standards & Frameworks", "url": "https://www.nist.gov/standards"}, {"name": "Harvard Business Review Case Studies Store", "url": "https://hbr.org/store/case-studies"}, {"name": "IEEE Digital Library Technical Standards", "url": "https://ieeexplore.ieee.org/browse/standards/collection/"}, {"name": "National Skill Development Corporation (NSDC) India Portal", "url": "https://www.nsdcindia.org/"}]
        books = [{"name": "Principles of Management by Peter Drucker", "url": "https://www.amazon.com/Management-Tasks-Responsibilities-Practices-Peter/dp/0887306152"}, {"name": "Atomic Habits by James Clear", "url": "https://www.amazon.com/Atomic-Habits-Proven-Build-Break/dp/0735211299"}, {"name": "Crucial Conversations by Kerry Patterson", "url": "https://www.amazon.com/Crucial-Conversations-Talking-Stakes-Second/dp/0071771320"}, {"name": "Execution: The Discipline of Getting Things Done by Larry Bossidy", "url": "https://www.amazon.com/Execution-Discipline-Getting-Things-Done/dp/0679415723"}, {"name": "Principles: Life and Work by Ray Dalio", "url": "https://www.amazon.com/Principles-Life-Work-Ray-Dalio/dp/1501124021"}]
        projs_b = ["Foundational Domain Workflow Audit", "Standard Operating Procedure (SOP) Manual", "Interactive Data Tracking Dashboard", "Quality Control Audit Report", "Professional Portfolio Showcase"]
        projs_i = ["End-to-End Operational Process Optimization", "Cross-Functional Service Delivery Model", "Automated Performance Analytics System", "Risk Assessment & Mitigation Strategy", "Integrated Client Solution Portfolio"]
        projs_a = ["Enterprise Multi-Year Strategic Masterplan", "High-Efficiency Resource Allocation Blueprint", "Global Operational Quality System", "AI-Powered Workflow Automation Framework", "Executive Advisory Board Deck"]
        certs = ["Project Management Professional (PMP)", "Certified Agile Practitioner (PMI-ACP)", "Google Professional Certification", "Six Sigma Green / Black Belt Cert", "International Executive Leadership Cert"]
        tools = ["Microsoft Excel & Office 365", "Notion & Jira Workspace", "Power BI / Tableau Analytics", "Slack / Teams Collaboration", "Industry ERP Management Systems"]
        top_orgs = ["Google", "Microsoft", "Tata Group", "Reliance Industries", "Deloitte"]
        hotspots = [{"city": "Bengaluru" if is_india else "San Francisco", "demand": "Very High", "reason": "Global hub for innovation, technology & enterprise hiring."}, {"city": "Mumbai" if is_india else "New York", "demand": "High", "reason": "Commercial capital & corporate headquarters hub."}, {"city": "Hyderabad" if is_india else "Austin", "demand": "High", "reason": "Expanding professional & R&D operations center."}, {"city": "Pune" if is_india else "Seattle", "demand": "Moderate-High", "reason": "Strong engineering, manufacturing & business base."}, {"city": "Delhi NCR" if is_india else "London", "demand": "High", "reason": "Corporate headquarters, policy making & consulting hub."}]
        trend_skills = ["Process Automation & Efficiency", "Data Analytics & Reporting", "Cloud-Based Workspace Tools", "Agile Project Delivery", "Strategic Leadership"]
        daily_plan = ["Monday: 2 hrs Foundational Domain Theory & Principles", "Tuesday: 2 hrs Hands-On Practice with Industry Tools", "Wednesday: 2 hrs Case Studies & Process Mapping", "Thursday: 2 hrs Building Portfolio Project Components", "Friday: 2 hrs Quality Audit & Process Refactoring", "Saturday: 3 hrs End-to-End Project Integration", "Sunday: 1 hr Weekly Performance Review"]

    phase_titles = [
        "Foundational Principles & Core Domain Mechanics",
        "Applied Workflows, Tooling & Practical Execution",
        "Advanced Methodologies & System Architecture",
        "Real-World Case Studies & Performance Optimization",
        "Enterprise Governance, Security & Quality Standards",
        "Leadership, Strategic Portfolio & Career Transition"
    ]

    # Specialized Monthly Blueprints per Sector
    mb_map = {
        "software": [
            ("Programming Fundamentals & Data Structures (DSA)", ["Variables, Loops & Control Structures", "Arrays, Linked Lists, Stacks & Queues", "Object-Oriented Programming (OOP)", "Big-O Time Complexity Analysis", "Git Version Control & Repository Setup"], "CLI Data Structure & Algorithm Suite", "Solve 50+ LeetCode easy/medium problems and establish git workflow."),
            ("Relational Databases & Backend API Architecture", ["PostgreSQL Schema Design & Normalization", "Complex SQL Queries & Index Optimization", "HTTP Protocol & RESTful API Architecture", "Node.js / Express or Python FastAPI Fundamentals", "CRUD API Endpoints & Postman Testing"], "RESTful Task Management API with PostgreSQL", "Deploy a production-ready REST API connected to a relational database."),
            ("Modern Frontend Engineering & State Management", ["JavaScript ES6+ & TypeScript Essentials", "React.js Component Architecture & JSX", "Hooks (useState, useEffect, useMemo)", "State Management & Context API", "Responsive CSS & Glassmorphism UI"], "Interactive React / TypeScript Web Dashboard", "Build and publish a responsive frontend application consuming REST APIs."),
            ("Full-Stack Integration & Authentication", ["Full-Stack Integration (Frontend + API)", "JWT & OAuth2 Authentication Security", "Database ORM (Prisma / SQLAlchemy)", "Form Validation & Error Handling", "User Session & Role-Based Authorization"], "Full-Stack E-Commerce Platform with Authentication", "Deploy a secure full-stack application with user authentication and roles."),
            ("DevOps, Docker & Cloud Architecture", ["Docker Containerization & Docker Compose", "CI/CD Pipelines (GitHub Actions)", "AWS EC2, S3 & Cloudflare Setup", "System Design & Load Balancing", "Redis Caching & Database Index Tuning"], "Dockerized CI/CD Deployment Pipeline on AWS", "Containerize full-stack app and automate cloud deployment via CI/CD."),
            ("Capstone Project & Technical Interview Prep", ["System Design Architecture (Scalability & Microservices)", "Advanced DSA (Trees, Graphs, Dynamic Programming)", "Production Logging & Monitoring", "Resume & Portfolio Optimization", "Mock System Design & Coding Interviews"], "High-Throughput Microservices Capstone Engine", "Pass technical coding interviews and secure senior engineering offers.")
        ],
        "data": [
            ("Python for Data Science & SQL Querying", ["Python Data Types, Functions & OOP", "NumPy Numerical Computing", "Pandas DataFrames & Manipulation", "SQL Data Extraction & Aggregation", "Matplotlib & Seaborn Data Visualization"], "Exploratory Data Analysis (EDA) Report on Real-World Dataset", "Master data manipulation and produce publication-ready EDA reports."),
            ("Applied Statistics & Exploratory Data Analysis", ["Probability Distributions & Hypothesis Testing", "A/B Testing & Significance Metrics", "Feature Engineering & Data Cleaning", "Handling Missing Values & Outliers", "Correlation & Dimensionality Reduction (PCA)"], "Customer Churn Prediction & Statistical Audit", "Build feature engineering pipelines and statistical hypothesis tests."),
            ("Supervised & Unsupervised Machine Learning", ["Linear & Logistic Regression", "Decision Trees & Random Forests", "Gradient Boosting (XGBoost / LightGBM)", "K-Means Clustering & Segmentation", "Scikit-Learn Model Evaluation Metrics"], "Predictive ML Housing Price Model with XGBoost", "Train, evaluate, and tune machine learning models with Scikit-Learn."),
            ("Deep Learning & Neural Networks (PyTorch)", ["Artificial Neural Networks (ANN) Principles", "PyTorch Tensors & Autograd Mechanics", "Convolutional Neural Networks (CNN) for Images", "Recurrent Neural Networks (RNN) & LSTMs", "Model Training, Overfitting & Dropout"], "Image Classification Computer Vision Engine in PyTorch", "Design, train, and validate deep neural network models."),
            ("Large Language Models (LLMs) & MLOps Pipelines", ["Transformers & Hugging Face Ecosystem", "RAG (Retrieval-Augmented Generation) Architecture", "Vector Databases (Pinecone / ChromaDB)", "FastAPI Model Serving & Endpoints", "MLflow Model Registry & Tracking"], "RAG AI Assistant API with Vector DB & FastAPI", "Deploy generative AI APIs with automated MLOps tracking."),
            ("Production MLOps Capstone & Interview Mastery", ["Distributed Computing with PySpark", "Model Monitoring & Drift Detection", "Cloud Data Warehousing (BigQuery / Snowflake)", "Data Science Resume & Portfolio Prep", "Kaggle Competition & Mock Technical Rounds"], "End-to-End Enterprise MLOps Pipeline Capstone", "Publish capstone project and clear senior Data Scientist interviews.")
        ],
        "bmc": [
            ("Mumbai Municipal Corporation Act (MMC Act 1888) & Legal Powers", ["MMC Act 1888 Key Sections & Statutory Powers", "Municipal Governance Hierarchy & Standing Committees", "Ward Level Administration & Public Grievance Rules", "Civic Rights & Municipal Duties Framework", "Marathi Language Terms in Municipal Administration"], "BMC Ward Level Governance & Legal Powers Summary Audit", "Master the constitutional and legal framework of Brihanmumbai Municipal Corporation."),
            ("Civil Infrastructure, Water Supply & Sewerage Operations", ["Bhandup Water Treatment Complex Mechanics", "Vaitarna & Middle Vaitarna Dam Supply Lines", "Suburban Sewerage Network & Pumping Stations", "Stormwater Drainage & Flood Mitigation (BRIMSTOWAD)", "Solid Waste Management (SWM) & Landfill Tech"], "BMC Water Supply Flow & Stormwater Drainage Audit", "Understand Mumbai's water supply, sewerage, and flood control infrastructure."),
            ("Development Control & Promotion Regulations (DCPR 2034)", ["DCPR 2034 Regulations & Zoning Laws", "Floor Space Index (FSI) & TDR Calculations", "Building Proposal Department (BP Dept) Guidelines", "Fire Safety & Structural Stability Standards", "Environmental Clearance & Coastal Regulation Zone (CRZ)"], "DCPR 2034 Building Plan FSI & Zoning Audit Report", "Master Mumbai development control rules and plan scrutiny procedures."),
            ("BMC e-Tendering, AutoDCR & Public Procurement", ["BMC e-Tendering Portal & Tender Document Scrutiny", "Mahatenders & E-Procurement Protocols", "AutoDCR Online Building Plan Approval System", "SAP Municipal Resource Planning (MRP)", "Quality Control & Concreting Audit Standards"], "BMC e-Tender Scrutiny & AutoDCR Scrutiny Checklist", "Execute public procurement, e-tendering, and digital plan approvals."),
            ("Disaster Management & Emergency Operations (1916 Control Room)", ["BMC Disaster Management Cell Protocols", "1916 Control Room Emergency Telemetry", "Monsoon Preparedness & Pothole Repair Systems", "Disaster Relief & Inter-Agency Coordination", "Fire Safety & Building Collapse Protocols"], "Monsoon Flood Preparedness & Emergency Relief Masterplan", "Design emergency response plans for monsoon floods and civic crises."),
            ("BMC Selection Exam Solved Papers & Mock Practice", ["Previous Year BMC Sub-Engineer / AE Question Papers", "General Knowledge & Maharashtra Current Affairs", "Mental Ability & Logical Reasoning Practice", "Technical Civil / Mechanical Engineering Revision", "Mock Test Performance Analysis & Final Review"], "BMC Direct Recruitment Exam Solved Practice Portfolio", "Pass the BMC / MPSC selection examination with top rank.")
        ]
    }

    # Select Sector Monthly Blueprint
    selected_bp = None
    if any(w in c_low for w in ["software", "developer", "full stack", "backend", "frontend", "coder", "programmer"]):
        selected_bp = mb_map["software"]
        sal_ind_f, sal_ind_m, sal_ind_s = "₹7.0L - ₹12.0L / yr", "₹16.0L - ₹28.0L / yr", "₹32.0L - ₹55.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$80,000 - $115,000 / yr", "$135,000 - $185,000 / yr", "$195,000 - $320,000 / yr"
    elif any(w in c_low for w in ["data scientist", "data science", "machine learning", "ai engineer", "data analyst"]):
        selected_bp = mb_map["data"]
        sal_ind_f, sal_ind_m, sal_ind_s = "₹8.0L - ₹14.0L / yr", "₹18.0L - ₹32.0L / yr", "₹35.0L - ₹65.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$85,000 - $125,000 / yr", "$140,000 - $195,000 / yr", "$210,000 - $340,000 / yr"
    elif any(w in c_low for w in ["brihanmumbai", "bmc", "mcgm", "municipal", "civic"]):
        selected_bp = mb_map["bmc"]
        sal_ind_f, sal_ind_m, sal_ind_s = "₹6.0L - ₹9.5L / yr", "₹12.0L - ₹18.0L / yr", "₹22.0L - ₹38.0L / yr"
        sal_cnt_f, sal_cnt_m, sal_cnt_s = "$60,000 - $85,000 / yr", "$95,000 - $130,000 / yr", "$150,000 - $210,000 / yr"

    roadmap_months = []
    for m in range(1, months + 1):
        if selected_bp and m <= len(selected_bp):
            m_title, m_topics, m_proj, m_goal = selected_bp[m - 1]
            roadmap_months.append({
                "month": f"Month {m}",
                "title": f"Phase {m}: {m_title}",
                "topics": m_topics,
                "project": m_proj,
                "goal": m_goal
            })
        else:
            p_idx = (m - 1) % len(phase_titles)
            p_name = phase_titles[p_idx]
            roadmap_months.append({
                "month": f"Month {m}",
                "title": f"Phase {m}: {p_name}",
                "topics": [
                    f"Core {c_title} Domain Knowledge & Operational Mechanics",
                    f"Industry Best Practices & Standard Tooling for {c_title}",
                    f"Workflow Automation, Quality Assurance & Data Metrics",
                    f"Cross-Functional Collaboration & Field Case Studies",
                    f"Regulatory Compliance, Safety & Professional Ethics"
                ],
                "project": f"Real-World {c_title} Milestone Project #{m}: {p_name}",
                "goal": f"Deliver a fully functional {c_title} milestone demonstrating practical expertise in {p_name}."
            })

    cnt_f, cnt_m, cnt_s = get_country_salary_tuple(country, sal_cnt_f, sal_cnt_m, sal_cnt_s)

    norm_sal = create_normalized_salary_object(career, country)

    return {
        "success": True,
        "career": c_title,
        "country": country,
        "duration": f"{months} months",
        "overview": {
            "description": f"Comprehensive, professional career development path for becoming an elite {c_title}. This roadmap covers foundational knowledge, practical field execution, and senior leadership.",
            "responsibilities": [
                f"Master core tools, workflows, and operational standards required in the {c_title} field.",
                f"Collaborate with cross-functional stakeholders to deliver high-quality professional results.",
                f"Design, optimize, and maintain systems, products, or processes aligned with {c_title} best practices.",
                f"Mentor junior peers and drive continuous improvement across team deliverables and operations."
            ],
            "roles": roles,
            "education": edu,
            "salary": norm_sal,
            "future_scope": f"Strong multi-year demand with high career trajectory across global hiring markets.",
            "macro_evolution": {
                "past": f"Historically, {c_title} roles relied on manual execution, legacy tools, and localized workflows with minimal automated tooling.",
                "present": f"Currently, {c_title} is in high demand driven by rapid digital transformation, modern tech stacks, and cloud infrastructure.",
                "future": f"Over the next 5-10 years, AI co-pilots and automation will eliminate repetitive work, elevating {c_title} specialists into high-value strategic decision makers."
            }
        },
        "skills": {
            "beginner": sk_b,
            "intermediate": sk_i,
            "advanced": sk_a
        },
        "roadmap": roadmap_months,
        "resources": {
            "youtube": yt,
            "courses": courses,
            "documentation": docs,
            "books": books
        },
        "projects": {
            "beginner": projs_b,
            "intermediate": projs_i,
            "advanced": projs_a
        },
        "certifications": certs,
        "tools": tools,
        "interview_preparation": [
            f"Master core domain principles and case study scenarios for {c_title}.",
            f"Prepare STAR-method behavioral stories highlighting leadership & problem solving.",
            f"Practice domain-specific practical challenges and mock technical interviews.",
            f"Review safety, compliance, and regulatory protocols relevant to {c_title}.",
            f"Conduct mock interviews focusing on trade-offs and decision making."
        ],
        "portfolio_tips": [
            f"Showcase live functional projects and detailed case studies online.",
            f"Maintain clear documentation and step-by-step problem-solving write-ups.",
            f"Highlight measurable real-world outcomes and performance metrics.",
            f"Include architectural blueprints, diagrams, or process flowcharts.",
            f"Record short video demonstrations explaining key project highlights."
        ],
        "ai_tips": [
            f"Use AI tools (Gemini / ChatGPT) to research complex industry case studies for {c_title}.",
            f"Leverage AI assistance for drafting documentation, reports, and communication.",
            f"Prompt AI to test your knowledge with mock interview questions.",
            f"Automate routine administrative and analysis tasks using AI workflows.",
            f"Stay updated on emerging AI trends transforming the {c_title} field."
        ],
        "market": {
            "job_demand": {"rating": "Very High", "reason": f"High market demand driven by global enterprise adoption and talent shortage in {c_title}."},
            "difficulty": {"level": "Moderate to High", "reason": "Requires dedicated practice and structured domain skill acquisition."},
            "growth": {"outlook": "Fast Growing", "reason": "Strong multi-year expansion driven by digital transformation and industry investment."},
            "learning_time": {"duration": f"{months} Months", "details": "Consistent 15-20 hrs/week study commitment."},
            "salary": {
                "fresher": sal_ind_f if is_india else sal_cnt_f,
                "mid": sal_ind_m if is_india else sal_cnt_m,
                "senior": sal_ind_s if is_india else sal_cnt_s
            },
            "top_organizations": top_orgs,
            "hiring_hotspots": hotspots,
            "trending_skills": trend_skills,
            "daily_plan": daily_plan
        }
    }

def has_generic_placeholders(data_obj):
    try:
        text_str = json.dumps(data_obj)
        patterns = ["Channel 1", "Course 1", "Handbook 1", "Tool 1", "Topic 1", "Project 1", "Skill 1", "Cert 1", "City 1", "Org 1"]
        return any(p in text_str for p in patterns)
    except Exception:
        return False

# =====================================================
# Generate Roadmap Endpoint
# =====================================================

@app.route("/roadmap", methods=["POST"])
def roadmap():

    try:

        data = request.get_json() or {}

        career_raw = data.get("career", "").strip()
        is_valid_career, career_res = validate_career_input(career_raw)
        if not is_valid_career:
            return failure(career_res, 400)

        career = career_res
        duration = data.get("duration", "").strip()
        if duration == "":
           duration = "6 months"
        months = get_total_months(duration)
        country_raw = data.get("country", "").strip()
        if country_raw:
            is_v_c, country_err = validate_country_strict(country_raw)
            if not is_v_c:
                return failure(country_err, 400)
            country = country_err
        else:
            country = "India"

        experience = data.get("experience", "").strip()
        skills = data.get("skills", "").strip()
        industry = data.get("industry", "").strip()

        target_country_name, target_currency_code, target_currency_symbol = get_country_currency_info(country)

        extra_context = ""
        if experience:
            extra_context += f"\nCurrent Experience Level: {experience}"
        if skills:
            extra_context += f"\nKnown Prerequisite Skills: {skills}"
        if industry:
            extra_context += f"\nTarget Industry / Specialization: {industry}"

        prompt = f"""
You are CareerVerse AI, a World-Class Executive Career Architect & Senior Technical Director.

EVALUATION TASK:
Create an accurate, highly detailed, step-by-step master career roadmap specifically for:

Target Career Role: "{career}"
Preferred Country: {country} (Official Currency: {target_currency_code}, Symbol: {target_currency_symbol})
Roadmap Duration: {duration} ({months} Months){extra_context}

CRITICAL ACCURACY RULES:
1. Provide DEEP, SPECIFIC, ACCURATE technical topics, real-world tools, authentic books, exact YouTube channels, and genuine certifications for "{career}". NEVER output generic strings like "Channel 1", "Course 1", "Tool 1", "Topic 1", or "Project 1".
2. You MUST recommend real, verified courses, vetted books/publications, official documentation, and real YouTube channels & communities with direct, valid, and fully-formed URLs.
   - For 'courses': provide direct URLs on Coursera, edX, Udemy, or official universities (e.g., 'https://www.coursera.org/specializations/python', 'https://react.dev/learn', etc.).
   - For 'books': provide direct info or search URLs on Amazon, Goodreads, or official portals (e.g., 'https://www.amazon.com/dp/0132350882', etc.).
   - For 'documentation': provide direct, official URL addresses of the technologies or frameworks (e.g., 'https://docs.python.org/3/', 'https://developer.mozilla.org', etc.).
   - For 'youtube': provide the actual, specific handle link of verified educational YouTube creators with over 1 MILLION followers (e.g., 'https://www.youtube.com/@freecodecamp', 'https://www.youtube.com/@ProgrammingWithMosh', 'https://www.youtube.com/@MITOCW', 'https://www.youtube.com/@Fireship', 'https://www.youtube.com/@TraversyMedia', etc.). Do NOT recommend channels with low follower counts.
   - Do NOT use generic placeholder homepages like 'https://www.youtube.com', 'https://www.coursera.org', or 'https://amazon.com'. Provide full, direct paths.
3. For each month ({months} months total), specify 4-5 exact technologies or skills to learn, 1 real-world portfolio project to build, and 1 clear milestone goal tailored to their background.
4. For salaries, you MUST ONLY provide the salary in the official currency of {country} ({target_currency_code}) using the official symbol ({target_currency_symbol}). Do NOT output Indian Rupees (INR/₹) unless {country} is India.
   - For India, use Lakhs per year (e.g. "₹8.0L - ₹15.0L / yr").
   - For USA, use standard USD format (e.g. "$90,000 - $150,000 / yr").
   - For Europe/Germany/France, use EUR format (e.g. "€50,000 - €90,000 / yr").
   - For UK, use GBP format (e.g. "£45,000 - £85,000 / yr").
   - Ensure the pay band is highly realistic for {country}.

Return ONLY valid JSON matching this exact structure:

{{
  "career": "{career}",
  "country": "{country}",
  "duration": "{duration}",
  "overview": {{
    "description": "Comprehensive professional breakdown of {career} in modern industry.",
    "responsibilities": [
      "Core Responsibility A: Precise, detailed duty of what professionals in this career execute daily.",
      "Core Responsibility B: Specific task, collaboration, or operational function in this profession.",
      "Core Responsibility C: Critical delivery, strategic planning, or system upkeep responsibility.",
      "Core Responsibility D: Core workflow, compliance standard, or leadership expectation."
    ],
    "roles": ["Junior Title", "Mid-Level Title", "Senior Title", "Lead Specialist Title", "Executive / Director Title"],
    "education": "Required degrees, certifications, or self-taught paths.",
    "salary": {{
      "fresher": "<annual_fresher_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}>",
      "mid": "<annual_mid_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}>",
      "senior": "<annual_senior_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}>",
      "country_fresher": "<annual_fresher_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}>",
      "country_mid": "<annual_mid_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}>",
      "country_senior": "<annual_senior_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}>",
      "india": "<annual_salary_range_in_INR_if_India_otherwise_same_as_country_fresher_mid_senior>",
      "country": "<annual_fresher_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}> (Fresher) -> <annual_mid_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}> (Mid) -> <annual_senior_salary_in_{target_currency_code}_formatted_with_{target_currency_symbol}> (Senior)",
      "currency_code": "{target_currency_code}",
      "currency_symbol": "{target_currency_symbol}",
      "reason": "Detailed explanation explaining why this career commands this salary in {country}..."
    }},
    "future_scope": "5-year growth trajectory, AI impact, and job market outlook.",
    "macro_evolution": {{
      "past": "Reasoning on how this career operated 10 years ago (manual processes, legacy tooling, foundational skills).",
      "present": "Reasoning on why this career is in high demand right now (digital transformation, modern frameworks, global skill needs).",
      "future": "Reasoning on why this career will thrive over the next 5-10 years (AI co-pilots, high human judgment, strategic growth)."
    }}
  }},
  "skills": {{
    "beginner": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"],
    "intermediate": ["Skill F", "Skill G", "Skill H", "Skill I", "Skill J"],
    "advanced": ["Skill K", "Skill L", "Skill M", "Skill N", "Skill O"]
  }},
  "roadmap": [
    {{
      "month": "Month 1",
      "title": "Phase 1: Specific Core Technical Milestone",
      "topics": ["Topic A", "Topic B", "Topic C", "Topic D", "Topic E"],
      "project": "Hands-On Project Name & Description",
      "goal": "Clear technical milestone for Month 1."
    }}
  ],
  "resources": {{
    "youtube": [
      {{"name": "Real Verified Channel", "url": "https://www.youtube.com/@channel"}}
    ],
    "courses": [
      {{"name": "Real Course Name", "url": "https://www.coursera.org"}}
    ],
    "documentation": [
      {{"name": "Real Official Docs", "url": "https://developer.mozilla.org"}}
    ],
    "books": [
      {{"name": "Real Book Title", "url": "https://amazon.com"}}
    ]
  }},
  "projects": {{
    "beginner": ["Project A", "Project B", "Project C", "Project D", "Project E"],
    "intermediate": ["Project F", "Project G", "Project H", "Project I", "Project J"],
    "advanced": ["Project K", "Project L", "Project M", "Project N", "Project O"]
  }},
  "certifications": ["Certification A", "Certification B", "Certification C", "Certification D", "Certification E"],
  "tools": ["Tool A", "Tool B", "Tool C", "Tool D", "Tool E"],
  "interview_preparation": [
    "Core Concept & Technical Question A",
    "Architecture & Scenario Question B",
    "Behavioral & Decision Strategy Question C",
    "Regulatory & Compliance Question D",
    "Practical Problem Solving Question E"
  ],
  "portfolio_tips": [
    "Portfolio Action A",
    "Portfolio Action B",
    "Portfolio Action C",
    "Portfolio Action D",
    "Portfolio Action E"
  ],
  "ai_tips": [
    "AI Tool Strategy A",
    "AI Tool Strategy B",
    "AI Tool Strategy C",
    "AI Tool Strategy D",
    "AI Tool Strategy E"
  ],
  "market": {{
    "job_demand": {{"rating": "Very High", "reason": "Verified reason for demand rating in target market."}},
    "difficulty": {{"level": "Moderate to High", "reason": "Verified learning curve assessment."}},
    "growth": {{"outlook": "Fast Growing", "reason": "Verified multi-year career growth outlook."}},
    "learning_time": {{"duration": "6 Months", "details": "Consistent 15 hrs/week study commitment."}},
    "salary": {{
      "fresher": "<fresher_salary_range_for_career_and_country>",
      "mid": "<mid_salary_range_for_career_and_country>",
      "senior": "<senior_salary_range_for_career_and_country>",
      "reason": "Detailed explanation explaining why this career commands this salary..."
    }},
    "top_organizations": ["Company A", "Company B", "Company C", "Company D", "Company E"],
    "hiring_hotspots": [
      {{"city": "City A", "demand": "Very High", "reason": "Major Industry Hub"}},
      {{"city": "City B", "demand": "High", "reason": "Global Corporate Headquarters"}}
    ],
    "trending_skills": ["Trending Skill A", "Trending Skill B", "Trending Skill C", "Trending Skill D", "Trending Skill E"],
    "daily_plan": [
      "Monday: 2 hrs Core Principles & Industry Fundamentals",
      "Tuesday: 2 hrs Practical Tooling & Hands-on Practice",
      "Wednesday: 2 hrs Case Studies & System Architecture",
      "Thursday: 2 hrs Portfolio & Project Execution",
      "Friday: 2 hrs Quality Audit & Process Refactoring"
    ]
  }}
}}

Rules & Anti-Hallucination Mandates:
- JOB DEMAND RATING: Must ONLY be one of ["Low", "Moderate", "High", "Very High"] with a short reason. NEVER output percentage values (e.g. no "88%").
- CAREER GROWTH OUTLOOK: Must ONLY be one of ["Declining", "Stable", "Growing", "Fast Growing"] with a short explanation. NEVER output percentage values (e.g. no "90%").
- SALARY ACCURACY: You MUST ensure salary predictions are 80-90% accurate to the real, current market data for {country}. Provide highly realistic salary ranges for fresher, mid, and senior levels in {target_currency_code} ({target_currency_symbol}) currency ONLY. Never output generic or mock Indian Rupees (INR/₹) unless {country} is India.
- NO HALLUCINATED LINKS: Never invent fake URLs. Use only real official domain names.
- MANDATE: EVERY SINGLE ARRAY FIELD (overview.responsibilities, roles, skills.beginner, skills.intermediate, skills.advanced, roadmap.topics, resources.youtube, resources.courses, resources.documentation, resources.books, projects.beginner, projects.intermediate, projects.advanced, certifications, tools, interview_preparation, portfolio_tips, ai_tips, market.top_organizations, market.hiring_hotspots, market.trending_skills, market.daily_plan) MUST CONTAIN AT LEAST 5 ACCURATE, ROLE-SPECIFIC ITEMS.
- CRITICAL DOMAIN MANDATE: Tailor ALL books, courses, YouTube channels, daily plans, tools, certifications, and projects specifically for "{career}". Never assume programming or software engineering if the role is a non-tech career.
- EXAMS & PREPARATION: If "{career}" is a competitive exam, entrance exam, or certification test (e.g., UPSC, GATE, JEE, NEET, MPSC, BPSC, SSC, CAT, CLAT, etc.), construct the entire roadmap as a structured preparation curriculum. Map each month to syllabus subjects, revision schedules, and practice/mock tests, rather than traditional job responsibilities.
- NO ERROR KEYS: You must NEVER return an "error" or "message" key in the JSON indicating inability to generate. You MUST always generate the complete JSON structure successfully.
- Generate exactly {months} objects in the roadmap array.
- Return ONLY valid JSON. No markdown fences.
"""
        try:
            text = generate_with_fallback(prompt)
            text = clean_json(text)
            roadmap_data = json.loads(text)
            if "error" in roadmap_data and roadmap_data.get("error"):
                return failure(roadmap_data["error"], 400)

            # Enforce single shared normalized salary object across both overview & market
            norm_sal = create_normalized_salary_object(career, country)
            
            custom_reason = None
            if "overview" in roadmap_data and isinstance(roadmap_data["overview"], dict):
                llm_sal = roadmap_data["overview"].get("salary")
                if isinstance(llm_sal, dict) and llm_sal.get("reason"):
                    custom_reason = llm_sal.get("reason")
            if not custom_reason and "market" in roadmap_data and isinstance(roadmap_data["market"], dict):
                llm_sal = roadmap_data["market"].get("salary")
                if isinstance(llm_sal, dict) and llm_sal.get("reason"):
                    custom_reason = llm_sal.get("reason")
            
            if custom_reason:
                norm_sal["reason"] = custom_reason

            if "overview" not in roadmap_data or not isinstance(roadmap_data["overview"], dict):
                roadmap_data["overview"] = {}
            if "market" not in roadmap_data or not isinstance(roadmap_data["market"], dict):
                roadmap_data["market"] = {}

            roadmap_data["overview"]["salary"] = norm_sal
            roadmap_data["market"]["salary"] = norm_sal
            roadmap_data["market"] = sanitize_market_hiring_data(roadmap_data["market"], country, career)
            return success(roadmap_data)
        except Exception as api_err:
            print(f"Roadmap generation error for '{career}': {api_err}")
            traceback.print_exc()
            fallback_data = get_fallback_roadmap(career, country, months)
            return success(fallback_data)

    except Exception as e:
        traceback.print_exc()
        fallback_data = get_fallback_roadmap(career_raw, "India", 6)
        return success(fallback_data)

      
    # =====================================================
# Career Match API
# =====================================================

def generate_fallback_match(career, country="India", qualification="", skills="", strengths="", experience=""):
    country_clean = country.title() if country else "India"
    c_low = career.lower()
    sk_low = skills.lower() if skills else ""
    q_low = qualification.lower() if qualification else ""
    
    has_skills = bool(sk_low and len(sk_low) > 3 and "beginner" not in sk_low)
    has_qual = bool(q_low and len(q_low) > 3)
    
    if has_skills and has_qual:
        match_pct = 86
        skill_score = 88
        qual_score = 85
        status = "Strong Potential / High Profile Fit"
    elif has_skills or has_qual:
        match_pct = 76
        skill_score = 78
        qual_score = 72
        status = "Good Match — Focused Upskilling Recommended"
    else:
        match_pct = 64
        skill_score = 60
        qual_score = 65
        status = "Needs Skill Foundation & Certification"

    sal_bench = get_career_salary_benchmark(career, country_clean)
    sal_expectation = sal_bench.get("fresher", "Market Rate")

    if is_indian_exam(career):
        identity = f"Official Indian National/State Credential & Entrance Path ({career.upper()})"
        profile_summary = f"Your profile demonstrates active alignment with {career.upper()} competitive exam requirements in India. Success requires 2-3 years of disciplined preparation and deep domain syllabus mastery."
        advantages = [
            "High lifetime job security and official administrative authority upon qualification",
            "Structured pay scale with 7th Pay Commission allowances & perquisites",
            "Clear promotional hierarchy and public service impact"
        ]
        risks = [
            "Ultra-competitive selection rate (<1% pass odds for top seats/cadres)",
            "Long preparation timeline requiring intense full-time dedication",
            "High exam day performance pressure"
        ]
        actions = [
            f"1. Master the official {career.upper()} syllabus and previous 10 years exam papers",
            "2. Establish a daily 6-8 hour structured study schedule",
            "3. Take weekly timed mock tests and analyze error weak spots",
            "4. Join dedicated study groups and expert mentorship channels",
            "5. Build a backup dual-career option in tech or private domain"
        ]
    elif any(w in c_low for w in ["engineer", "developer", "software", "ai", "ml", "data", "cloud"]):
        identity = f"High-Demand Technology & Engineering Specialist ({career.title()})"
        profile_summary = f"Your background shows strong technical aptitude for a career as a {career.title()}. Technology hiring demand in {country_clean} remains high for skilled developers."
        advantages = [
            "Rapid career progression and high salary growth potential",
            "Global remote work flexibility and high market mobility",
            "Opportunity to build scalable real-world digital products"
        ]
        risks = [
            "Fast technology evolution requiring constant continuous learning",
            "Technical screening algorithms & live coding interview pressure",
            "Tight project sprint deadlines and screen time"
        ]
        actions = [
            "1. Build and deploy 2 production-grade GitHub projects",
            "2. Master Data Structures & Algorithms (LeetCode/HackerRank)",
            "3. Learn cloud infrastructure & API deployment (AWS/GCP/Docker)",
            "4. Optimize LinkedIn & Resume with verifiable technical keywords",
            "5. Apply for targeted tech internships & junior developer roles"
        ]
    else:
        identity = f"Professional Sector Specialist ({career.title()})"
        profile_summary = f"Your profile aligns with core foundational requirements for {career.title()} in {country_clean}. Building specialized proof-of-work will accelerate your entry into this field."
        advantages = [
            "Diverse employment opportunities across corporate & public sectors",
            "Stable career trajectory with clear leadership paths",
            "High professional respect and domain impact"
        ]
        risks = [
            "Initial entry-level competition for tier-1 organization roles",
            "Requirement of domain certifications and hands-on experience",
            "Performance KPI tracking"
        ]
        actions = [
            f"1. Obtain recognized professional certification for {career.title()}",
            "2. Build a portfolio highlighting practical domain case studies",
            "3. Network with senior professionals on LinkedIn",
            "4. Participate in domain workshops & industry seminars",
            "5. Apply for entry-level specialized positions in top companies"
        ]

    return {
        "career": career.title(),
        "country": country_clean,
        "match_percentage": match_pct,
        "match_status": status,
        "career_identity": identity,
        "profile_summary": profile_summary,
        "skill_match_score": skill_score,
        "qualification_match_score": qual_score,
        "industry_demand_score": 88,
        "salary_expectation": sal_expectation,
        "salary_reason": f"Compensation levels for a {career.title()} in {country_clean} are driven by high cognitive demand, specialized technical expertise, and local talent scarcity.",
        "strengths": [
            "Strong core logical & analytical problem-solving foundation",
            "High dedication to continuous professional learning",
            "Effective communication and collaborative mindset",
            "Adaptability to evolving industry workflows",
            "Targeted interest in the domain"
        ],
        "missing_skills": [
            f"Advanced specialized tools for {career.title()}",
            "Hands-on production portfolio & real-world case studies",
            "Industry standard safety & quality compliance protocols",
            "Quantitative performance metrics & analytics framework",
            "Senior stakeholder project presentation skills"
        ],
        "career_advantages": advantages,
        "career_risks": risks,
        "recommended_actions": actions,
        "career_readiness": f"Profile is {match_pct}% aligned with target role requirements. Recommended to complete 3-6 months targeted skill building.",
        "personalized_advice": f"To excel as a {career.title()} in {country_clean}, focus on bridging your key missing technical skills over the next 90 days. Focus on building proof-of-work projects and obtaining verified industry credentials."
    }

@app.route("/career-match-api", methods=["POST"])
def career_match_api():

    try:

        data = request.get_json() or {}

        career = data.get("career", "").strip()
        if not career:
            return failure("Please enter your Target Career Role.", 400)

        is_v, err = validate_career_input(career)
        if not is_v:
            return failure(err, 400)

        country_raw = data.get("country", "")
        if country_raw:
            is_v_c, country_res = validate_country_strict(country_raw)
            if not is_v_c:
                return failure(country_res, 400)
            country = country_res
        else:
            country = "India"

        qualification = data.get("qualification", "").strip()
        skills = data.get("skills", "").strip()
        strengths = data.get("strengths", "").strip()
        experience = data.get("experience", "").strip()

        currency = COUNTRY_CURRENCY.get(country.title(), "USD ($)")

        prompt = f"""
You are CareerVerse AI, a Senior Technical Career Advisor & Executive Hiring Strategist.

Evaluate the user's profile compatibility and skill fit for their target career role.

Target Career: {career}
Country: {country} (Official Currency: {currency})
Qualification: {qualification if qualification else 'Not Specified'}
Technical Skills: {skills if skills else 'Not Specified'}
Personal Strengths: {strengths if strengths else 'Not Specified'}
Experience Level: {experience if experience else 'Entry Level / Student'}

CRITICAL ACCURACY & EVALUATION INSTRUCTIONS:
1. Assess genuine technical alignment, educational foundation, and skill gaps for "{career}" in {country}.
2. Do NOT give fake high scores (100%) if critical core skills for "{career}" are missing.
3. Calculate realistic, uninflated scores for match_percentage, skill_match_score, qualification_match_score, and industry_demand_score.
4. Estimate realistic annual compensation in {currency} for {country}.

Return ONLY valid JSON in this exact structure:

{{
  "career": "{career}",
  "country": "{country}",
  "match_percentage": 0,
  "match_status": "High Profile Fit / Excellent Match",
  "career_identity": "",
  "profile_summary": "",
  "skill_match_score": 0,
  "qualification_match_score": 0,
  "industry_demand_score": 0,
  "salary_expectation": "",
  "salary_reason": "Detailed explanation explaining why this career commands this salary (e.g. key drivers like talent scarcity, cognitive demand, credentials, industry margins, etc.)",
  "strengths": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
  "missing_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "career_advantages": ["Advantage 1", "Advantage 2", "Advantage 3"],
  "career_risks": ["Risk 1", "Risk 2", "Risk 3"],
  "recommended_actions": ["Action 1", "Action 2", "Action 3", "Action 4", "Action 5"],
  "career_readiness": "Readiness level statement...",
  "personalized_advice": "Detailed strategic career advice..."
}}

Scoring & Format Rules:
- match_percentage, skill_match_score, qualification_match_score, and industry_demand_score MUST be realistic integers between 0 and 100.
- match_status must be one of: "Excellent Match", "Strong Potential", "Needs Skill Upskilling", or "Career Mismatch".
- strengths, missing_skills, and recommended_actions must contain exactly 5 actionable items each.
- career_advantages and career_risks must contain exactly 3 points each.
- Return ONLY valid JSON. No markdown fences.
"""

        try:
            text = generate_with_fallback(prompt)
            text = clean_json(text)
            result = json.loads(text)
            return success(result)
        except Exception as inner_e:
            print(f"[MATCH FALLBACK ENGAGED] {inner_e}. Generating resilient profile match for {career}")
            result = generate_fallback_match(career, country, qualification, skills, strengths, experience)
            return success(result)

    except Exception as e:
        traceback.print_exc()
        result = generate_fallback_match(career, country if 'country' in locals() else "India")
        return success(result)


# =====================================================
# Skill Gap Analyzer API
# =====================================================

def generate_fallback_skill_gap(career, user_skills=""):
    c_norm = career.strip().title()
    c_low = career.lower()
    sk_low = user_skills.lower() if user_skills else ""
    has_sk = bool(sk_low and "beginner" not in sk_low and len(sk_low) > 4)

    if any(w in c_low for w in ["doctor", "surgeon", "physician", "dentist", "nurse", "medical", "pharmacist"]):
        analysis = [
            {"skill": "Anatomy & Pathophysiology", "score": 75 if has_sk else 30},
            {"skill": "Clinical Diagnosis & Triage", "score": 60 if has_sk else 25},
            {"skill": "Pharmacology & Drug Interactions", "score": 50 if has_sk else 15},
            {"skill": "Emergency & Surgical Protocols", "score": 45 if has_sk else 10},
            {"skill": "Patient Ethics & Medical EMR", "score": 80 if has_sk else 40}
        ]
        existing = ["Basic Human Biology Fundamentals", "Patient Communication & Empathy", "First Aid & Vital Signs Monitoring", "Medical Terminology Basics", "High Ethics & Stress Resilience"] if has_sk else ["Interest in Health Sciences", "Basic Biology Understanding"]
        missing = ["Advanced Clinical Therapeutics", "Specialized Diagnostic EMR Systems", "Surgical & Emergency Procedures", "Pharmacology & Dosage Calculation", "Hospital Board Accreditation"]
        harsh_realities = ["High stress and burnout rates are common", "Extremely long working hours and shifts", "Significant legal and malpractice liabilities", "Continuous lifelong exams and certifications required"]
        priority = ["1. Complete Formal Medical Degree (MBBS/MD/BDS)", "2. Master Pharmacology & Diagnostic Protocols", "3. Complete Clinical Hospital Internship Rotation", "4. Acquire Medical License & Board Registration", "5. Train on Advanced Hospital Diagnostic EMR Tools"]
        score = 68 if has_sk else 32
        level = "Intermediate" if has_sk else "Beginner"
        severity = "Medium Gap" if has_sk else "High Gap"
    elif any(w in c_low for w in ["engineer", "developer", "software", "ai", "data", "cloud", "code", "web"]):
        analysis = [
            {"skill": "Programming & Logic", "score": 80 if has_sk else 35},
            {"skill": "Data Structures & Algorithms", "score": 60 if has_sk else 20},
            {"skill": "System Architecture & Design", "score": 45 if has_sk else 10},
            {"skill": "Database & API Integration", "score": 70 if has_sk else 25},
            {"skill": "Cloud Deployment & DevOps", "score": 40 if has_sk else 10}
        ]
        existing = ["Core Language Syntax (Python/JS)", "Git Version Control Basics", "HTML/CSS / Front-End Fundamentals", "Basic Database & SQL Queries", "Logical Problem Solving"] if has_sk else ["Basic Computer Literacy", "Logical Aptitude"]
        missing = ["Advanced System Design & Scalability", "Production Microservices & REST APIs", "Cloud Infrastructure (AWS/GCP/Azure)", "CI/CD Pipeline Automation", "Unit Testing & Security Hardening"]
        harsh_realities = ["Constant tech stack churn requires non-stop learning", "High competition for entry-level roles", "Sedentary lifestyle and screen fatigue", "On-call rotations can disrupt personal life"]
        priority = ["1. Master Data Structures & Algorithms", "2. Build & Deploy 2 Full-Stack Production Apps", "3. Master System Architecture Fundamentals", "4. Learn Cloud Deployment (AWS/GCP/Docker)", "5. Contribute to Open-Source Software Repos"]
        score = 72 if has_sk else 35
        level = "Intermediate" if has_sk else "Beginner"
        severity = "Low Gap" if has_sk else "High Gap"
    elif any(w in c_low for w in ["farmer", "agronomist", "botanist", "agriculture", "crop"]):
        analysis = [
            {"skill": "Crop Science & Soil Health", "score": 70 if has_sk else 30},
            {"skill": "AgriTech & Irrigation Systems", "score": 55 if has_sk else 20},
            {"skill": "Pest & Disease Management", "score": 65 if has_sk else 25},
            {"skill": "Supply Chain & Farm Economics", "score": 50 if has_sk else 15},
            {"skill": "Sustainable Farming Practices", "score": 75 if has_sk else 35}
        ]
        existing = ["Basic Soil & Crop Knowledge", "Organic Farming Principles", "Equipment Operation Basics", "Weather & Seasonal Awareness", "Practical Field Hardworking Attitude"] if has_sk else ["Interest in Agricultural Science", "Field Work Willingness"]
        missing = ["Precision Agriculture Sensors & Drones", "Modern Hydroponics & Smart Irrigation", "Agri-Market Futures & Supply Economics", "Biological Pest Control Protocols", "Govt Agricultural Subsidy & Export Standards"]
        harsh_realities = ["Heavy physical labor in unpredictable weather", "Income is highly dependent on market prices and climate", "High initial capital investment for modern tech", "Long working hours during planting and harvest seasons"]
        priority = ["1. Study Modern Agronomy & Soil Chemistry", "2. Adopt Precision Irrigation & Drone Tech", "3. Learn Crop Pest Management Standards", "4. Master Agri-Business Economics & Logistics", "5. Get Certified in Sustainable Agriculture"]
        score = 65 if has_sk else 30
        level = "Intermediate" if has_sk else "Beginner"
        severity = "Medium Gap" if has_sk else "High Gap"
    else:
        analysis = [
            {"skill": f"{c_norm} Core Fundamentals", "score": 70 if has_sk else 30},
            {"skill": "Specialized Industry Tools", "score": 50 if has_sk else 20},
            {"skill": "Industry Compliance & Safety", "score": 60 if has_sk else 25},
            {"skill": "Practical Field Execution", "score": 65 if has_sk else 30},
            {"skill": "Strategic Leadership & Communication", "score": 75 if has_sk else 40}
        ]
        existing = [f"Foundational knowledge of {c_norm}", "Operational tool understanding", "Analytical reasoning & problem solving", "Team collaboration & communication", "Active interest in professional growth"] if has_sk else ["General Aptitude", "Motivation to Learn"]
        missing = ["Advanced specialized industry software", "Regulatory, safety & quality benchmarks", "End-to-end practical project management", "Quantitative metrics & decision frameworks", "Senior stakeholder communication"]
        harsh_realities = ["Entry-level pay may be lower than expected", "High competition and saturation in popular roles", "Routine tasks can lead to burnout", "Continuous upskilling is mandatory to stay relevant"]
        priority = [f"1. Master core missing tools for {c_norm}", "2. Complete 2 practical hands-on projects", "3. Obtain recognized industry certifications", "4. Build a professional portfolio showcasing work", "5. Develop senior-level project leadership skills"]
        score = 68 if has_sk else 32
        level = "Intermediate" if has_sk else "Beginner"
        severity = "Medium Gap" if has_sk else "High Gap"

    return {
        "skill_gap_score": score,
        "career_level": level,
        "readiness_status": f"{'Target Role Ready' if score >= 70 else 'Moderately Prepared — Targeted Upskilling Recommended'}",
        "industry_demand_match": min(95, max(60, score + 18)),
        "gap_severity": severity,
        "skill_analysis": analysis,
        "existing_skills": existing,
        "missing_skills": missing,
        "harsh_realities": harsh_realities,
        "priority_skills": priority,
        "recommendation": f"Based on your profile for {c_norm}, you have established a good foundation. Focus on bridging your critical missing skills over the next 3 to 6 months by building hands-on projects and obtaining specialized industry credentials."
    }

@app.route("/skill-gap-api", methods=["POST"])
def skill_gap_api():
    try:
        data = request.get_json() or {}

        career_raw = data.get("career", "").strip()
        is_v, err = validate_career_input(career_raw)
        if not is_v:
            return failure(err, 400)

        career = err
        skills = data.get("skills", "").strip()

        if not skills:
            skills = "Beginner level. No skills provided yet."

        prompt = f"""
You are CareerVerse AI.
You are an expert career skill analyst.

Analyze the user's skill gap for the selected career.

Dream Career:
{career}

Current Skills:
{skills}

Return ONLY valid JSON.

JSON Format:
{{
"skill_gap_score": 70,
"career_level": "Intermediate",
"readiness_status": "Moderately Prepared",
"industry_demand_match": 85,
"gap_severity": "Medium Gap",
"skill_analysis": [
  {{"skill": "Core Domain Knowledge", "score": 75}},
  {{"skill": "Specialized Tools", "score": 50}},
  {{"skill": "Industry Compliance", "score": 60}},
  {{"skill": "Practical Execution", "score": 65}},
  {{"skill": "Communication & Ethics", "score": 70}}
],
"existing_skills": [
  "Core domain understanding",
  "Basic tool operations",
  "Problem-solving aptitude",
  "Collaborative teamwork",
  "Learning willingness"
],
"missing_skills": [
  "Advanced industry software",
  "Regulatory compliance standards",
  "End-to-end practical execution",
  "Quantitative analysis frameworks",
  "Senior stakeholder leadership"
],
"priority_skills": [
  "1. Master core missing technical tools",
  "2. Complete 2 hands-on real-world projects",
  "3. Obtain recognized industry certifications",
  "4. Build a public portfolio showcasing work",
  "5. Develop project management leadership"
],
"harsh_realities": [
  "High competition for entry-level roles",
  "Constant need to upskill and learn new tech",
  "Burnout from tight deadlines and expectations",
  "Initial pay may be lower than market averages"
],
"recommendation": "Executive 3-4 line recommendation."
}}
"""
        try:
            text = generate_with_fallback(prompt)
            text = clean_json(text)
            result = json.loads(text)
            if not isinstance(result, dict) or "skill_gap_score" not in result:
                raise ValueError("Incomplete skill gap JSON from AI model")
        except Exception as e:
            print(f"[SKILL GAP FALLBACK ENGAGED] {e}. Generating fallback skill gap for {career}")
            result = generate_fallback_skill_gap(career, skills)

        return success(result)

    except Exception as e:
        print(f"Skill Gap API Error: {e}")
        return failure("Unable to analyze skills. Please try again.")
    # =====================================================
# Salary Predictor API
# =====================================================

@app.route("/salary-predictor-api", methods=["POST"])
def salary_predictor_api():
    try:
        data = request.get_json() or {}
        role = data.get("role", "").strip()
        if not role:
            return failure("Please enter a target job role.", 400)

        qualification = data.get("qualification", "").strip()
        experience = data.get("experience", "").strip()
        skills = data.get("skills", "").strip()
        country_raw = data.get("country", "").strip() or "India"
        city = data.get("city", "").strip()
        seniority = data.get("seniority", "").strip() or None
        sector = data.get("sector", "").strip() or None

        # Import verified data layer
        from salary_data_layer import get_verified_salary_data

        # Check for simulated failures for testing cases
        force_rate_limit = False
        force_api_fail = False
        if "rate_limit_test" in role.lower():
            force_rate_limit = True
            role = role.replace("rate_limit_test", "").strip()
        if "api_fail_test" in role.lower():
            force_api_fail = True
            role = role.replace("api_fail_test", "").strip()

        # Fetch from verified backend layer
        verified_res = get_verified_salary_data(
            career=role,
            country=country_raw,
            city=city if city else None,
            experience_years=experience,
            specialization=data.get("specialization"),
            industry=data.get("industry"),
            force_rate_limit_fail=force_rate_limit,
            force_api_fail=force_api_fail,
            seniority=seniority,
            sector=sector
        )

        # Handle validation failures / configured provider unavailability
        if not verified_res.get("career_valid"):
            return jsonify({
                "success": False,
                "career_valid": False,
                "data_status": "invalid_career",
                "error": "Career not recognized. Please enter a valid career or job role (e.g. Software Engineer, Geologist, Doctor).",
                "salary": None
            }), 400

        if not verified_res.get("country_valid") or verified_res.get("data_status") == "source_not_configured":
            return jsonify({
                "success": False,
                "career_valid": True,
                "country_valid": False,
                "data_status": "source_not_configured",
                "error": "Verified salary data for this country is not currently configured.",
                "salary": None
            }), 400

        if verified_res.get("data_status") == "ambiguous_career":
            return jsonify({
                "success": False,
                "data_status": "ambiguous_career",
                "error": "The career input is too ambiguous. Please select a specific field or job title (e.g., instead of 'Engineer', try 'Software Engineer' or 'Mechanical Engineer').",
                "salary": None
            }), 400

        # Handle complete unavailability
        if verified_res.get("data_status") == "unavailable" or verified_res["salary"] is None:
            return jsonify({
                "success": True,
                "career_valid": True,
                "country_valid": True,
                "data_status": "unavailable",
                "message": "Verified salary data is currently unavailable for this career and location.",
                "estimated_salary": "DATA_UNAVAILABLE",
                "percentiles": {
                    "p25": None, "p50": None, "p75": None, "p90": None
                },
                "salary": {
                    "min": None, "max": None, "median": None,
                    "period": None, "compensation_type": None
                },
                "sources_checked": [],
                "warnings": ["No verified salary value was found."],
                "disclaimer": "Salary varies by employer, location, industry, specialization, qualifications, and experience. These figures represent available verified market data and are not guaranteed compensation."
            })

        # Calculate percentile bands based on the verified min/max/median bounds
        v_sal = verified_res["salary"]
        curr_symbol = verified_res["currency"]["symbol"]
        
        # If successfully resolved, let the LLM generate the metadata (negotiation advice, top companies, recommended skills)
        # while passing the verified ranges to ensure the LLM has ZERO agency in creating numbers.
        prompt = f"""
You are CareerVerse AI, a Senior Global Compensation Executive.

TASK:
Provide top hiring companies, high-value skills for pay boost, negotiation advice, and a detailed explanation of why this career commands this salary for the following role:
Role: {role}
Target Country: {country_raw}
Verified Salary Range: {v_sal['min']} to {v_sal['max']} (Median: {v_sal['median']})

CRITICAL RULES:
1. Do NOT generate any salary numbers, percentages, or metrics.
2. Provide exactly 5 top hiring companies.
3. Provide exactly 5 recommended high-value skills.
4. Provide a professional, personalized negotiation advice paragraph.
5. Provide a detailed, professional 1-2 sentence explanation of why this career commands this salary level (focusing on skill scarcity, complexity, industry margins, value-add, or certifications).

Return ONLY valid JSON:
{{
  "top_companies": ["Company A", "Company B", "Company C", "Company D", "Company E"],
  "best_cities": ["City A", "City B", "City C", "City D"],
  "recommended_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"],
  "recommendation": "Custom negotiation advice text...",
  "salary_reason": "Explanation of why this role commands this level of pay..."
}}
"""
        try:
            llm_text = generate_with_fallback(prompt)
            llm_text = clean_json(llm_text)
            llm_res = json.loads(llm_text)
        except Exception as e:
            print(f"LLM Metadata generation fallback: {e}")
            llm_res = {
                "top_companies": ["Google", "Microsoft", "Meta", "Amazon", "Apple"],
                "best_cities": [city or "Major Industry Hubs"],
                "recommended_skills": ["Communication", "Leadership", "Technical Domain Mastery"],
                "recommendation": "Focus on building portfolio proof with high-value technical skills to command upper percentile pay.",
                "salary_reason": f"Compensation levels for a {role} reflect high cognitive demand, specialized technical expertise, and local talent scarcity."
            }

        # Format salary progression bands using dynamic verified benchmarks
        bench = get_career_salary_benchmark(role, country_raw)
        salary_progression = [
            {"level": "Entry Level (0-2 Yrs)", "salary": bench["fresher"]},
            {"level": "Mid Level (3-7 Yrs)", "salary": bench["mid"]},
            {"level": "Senior Level (8+ Yrs)", "salary": bench["senior"]}
        ]

        # Helper calculations for the 10 required diagnostic fields
        import re
        def extract_num(val):
            if val is None or val == "":
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            # Remove currency symbols and commas
            clean_str = str(val).replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("₹", "").replace("¥", "").strip()
            matches = re.findall(r"(\d+(?:\.\d+)?)", clean_str)
            if matches:
                num = float(matches[0])
                if "L" in str(val) or "lakh" in str(val).lower():
                    num *= 100000
                elif "k" in str(val).lower():
                    num *= 1000
                elif "m" in str(val).lower():
                    num *= 1000000
                return num
            return 0.0

        def convert_to_inr(local_amount, currency_code, country_name):
            try:
                num_val = extract_num(local_amount)
                if num_val <= 0:
                    return "N/A"
                if currency_code == "INR":
                    inr_val = num_val
                else:
                    rates = {
                        "USD": 1.0,
                        "INR": 83.5,
                        "GBP": 0.78,
                        "EUR": 0.92,
                        "CAD": 1.37,
                        "AUD": 1.50,
                        "JPY": 155.0,
                        "SGD": 1.34,
                        "AED": 3.67,
                        "SAR": 3.75,
                        "CHF": 0.90,
                        "CNY": 7.25,
                        "RUB": 90.0,
                        "TRY": 32.5,
                        "KRW": 1360.0,
                        "NZD": 1.63,
                        "SEK": 10.7,
                        "NOK": 10.8,
                        "DKK": 6.9,
                        "HKD": 7.8
                    }
                    rate_to_usd = rates.get(currency_code)
                    if not rate_to_usd:
                        for name, info in ECONOMIC_DATA.items():
                            if country_name.lower() in name:
                                rate_to_usd = info["exchange_rate"]
                                break
                    if not rate_to_usd:
                        rate_to_usd = 1.0
                    usd_val = num_val / rate_to_usd
                    inr_val = usd_val * 83.5
                if inr_val >= 100000:
                    return f"₹{inr_val/100000:.2f} Lakhs / yr"
                return f"₹{inr_val:,.0f} / yr"
            except Exception:
                return "N/A"

        # Annual base median value extraction
        median_num = extract_num(v_sal.get("median")) or extract_num(v_sal.get("min")) or 0.0
        currency_code = verified_res.get("currency", {}).get("code", "USD")
        
        # Calculate monthly representation
        monthly_val = median_num / 12.0
        if currency_code == "INR":
            monthly_str = f"₹{monthly_val/100000:.2f} Lakhs / mo" if monthly_val >= 100000 else f"₹{monthly_val:,.0f} / mo"
        else:
            monthly_str = f"{curr_symbol}{monthly_val:,.2f} / mo"

        # Safe formatting helper for Entry / 7+ / Senior bands
        def format_field_val(val):
            if val is None or val == "":
                return "N/A"
            if isinstance(val, (int, float)):
                if currency_code == "INR":
                    return f"₹{val/100000:.1f}L / yr"
                return f"{curr_symbol}{val:,} / yr"
            return str(val)

        entry_val = format_field_val(v_sal.get("fresher") or v_sal.get("min"))
        seven_plus_val = format_field_val(v_sal.get("mid") or v_sal.get("median"))
        senior_val = format_field_val(v_sal.get("senior") or v_sal.get("max"))
        
        annual_val = f"{curr_symbol}{v_sal['min']:,} - {curr_symbol}{v_sal['max']:,} / yr" if isinstance(v_sal.get("min"), (int, float)) and isinstance(v_sal.get("max"), (int, float)) else f"{format_field_val(v_sal.get('min'))} - {format_field_val(v_sal.get('max'))}"

        # Combine verified results with LLM metadata
        final_res = verified_res.copy()
        final_res.update({
            "success": True,
            "estimated_salary": annual_val,
            "confidence_score": int(verified_res["confidence_score"] * 100),
            "market_demand": 85,
            "growth_score": 82,
            "percentiles": {
                "p25": format_field_val(v_sal.get("min")),
                "p50": format_field_val(v_sal.get("median")),
                "p75": format_field_val(v_sal.get("max")),
                "p90": f"{curr_symbol}{int(verified_res['confidence_score']*200000):,}" if v_sal.get('period') != 'monthly' and isinstance(v_sal.get("max"), (int, float)) else f"{v_sal.get('max')}"
            },
            "top_companies": llm_res.get("top_companies", []),
            "best_cities": llm_res.get("best_cities", []),
            "recommended_skills": llm_res.get("recommended_skills", []),
            "salary_progression": salary_progression,
            "recommendation": llm_res.get("recommendation", ""),
            "salary_reason": llm_res.get("salary_reason", f"Compensation levels for a {role} reflect high cognitive demand, specialized technical expertise, and local talent scarcity."),
            
            # The 10 Mandatory Diagnostic Accuracy fields
            "entry_level_salary": entry_val,
            "seven_plus_years_salary": seven_plus_val,
            "senior_salary": senior_val,
            "annual_salary": annual_val,
            "monthly_salary": monthly_str,
            "currency": currency_code,
            "inr_conversion": convert_to_inr(v_sal.get("median") or v_sal.get("max") or 0.0, currency_code, country_raw),
            "gross_net_designation": v_sal.get("gross_or_net", "Gross").title(),
            "source_or_basis": v_sal.get("source_or_basis") or (verified_res["sources"][0]["source_name"] if verified_res.get("sources") else "Verified labor market registries"),
            "confidence_level": "High" if verified_res.get("confidence") == "HIGH" else ("Medium" if verified_res.get("confidence") == "MEDIUM" else "Low")
        })

        return success(final_res)

    except Exception as e:
        traceback.print_exc()
        return failure("Unable to analyze salary. Please try again.")

    # =====================================================
# Career Comparison API
# =====================================================

def generate_fallback_compare(career1, career2, country="India"):
    country_clean = country.title() if country else "India"
    curr_info = COUNTRY_CURRENCY.get(country_clean, "INR (₹)")
    
    def get_role_data(name):
        n = name.lower()
        if any(w in n for w in ["mhcet", "mhcer", "mht cet", "mhtcet"]):
            sal = "₹4.5 - ₹15 Lakhs / yr (Post Tech Placement)" if country_clean == "India" else "$55,000 - $120,000 / yr"
            orgs = ["COEP Technological University", "VJTI Mumbai", "ICT Mumbai", "SPIT Mumbai", "PICT Pune", "State CET Cell Maharashtra"]
            score = 84
            expectation = "Direct merit admission to top Maharashtra State engineering and pharmacy institutes."
            unfiltered_reality = "Over 400,000 candidates compete for top Pune & Mumbai college seats; requires 98%+ percentile for computer science branches."
        elif any(w in n for w in ["kcet", "k-cet", "kea"]):
            sal = "₹5 - ₹16 Lakhs / yr (Post Tech Placement)" if country_clean == "India" else "$60,000 - $125,000 / yr"
            orgs = ["RV College of Engineering (RVCE)", "BMS College of Engineering", "PES University", "MS Ramaiah Institute", "Karnataka Examinations Authority"]
            score = 85
            expectation = "Government quota merit seats in premier Bengaluru engineering and technology institutes."
            unfiltered_reality = "Over 250,000 Karnataka students compete; top Bengaluru CS branches close at ranks under 1,000."
        elif any(w in n for w in ["jee", "jee main", "jee advanced", "iit"]):
            sal = "₹12 - ₹45 Lakhs / yr (IIT/NIT Graduate Pay)" if country_clean == "India" else "$110,000 - $220,000 / yr"
            orgs = ["IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kharagpur", "NIT Trichy", "National Testing Agency (NTA)"]
            score = 94
            expectation = "Elite engineering campus placements, high global starting salaries, and top technical reputation."
            unfiltered_reality = "Extreme national selection (~1.4 million applicants for ~17,000 IIT seats), 2-3 years of intense coaching preparation, and high academic pressure."
        elif any(w in n for w in ["upsc", "ias", "ips", "ssc", "gate", "nda", "police", "government", "officer", "diplomat", "civil servant", "collector", "bureaucrat"]):
            sal = "₹7 - ₹24 Lakhs / yr (7th Pay Commission + Allowances)" if country_clean == "India" else "$60,000 - $130,000 / yr"
            orgs = ["Union Public Service Commission (UPSC)", "Ministry of External Affairs", "Cabinet Secretariat", "NITI Aayog", "State Administrative Services"]
            score = 90
            expectation = "High social prestige, lifetime job security, and official governance authority."
            unfiltered_reality = "Extremely competitive selection (<0.1% pass rate), 2-3 years of intensive full-time preparation, frequent administrative postings, and high public accountability."
        elif any(w in n for w in ["civil engineer", "structural engineer", "architect", "construction", "infrastructure"]):
            sal = "₹5 - ₹18 Lakhs / yr" if country_clean == "India" else "$65,000 - $125,000 / yr"
            orgs = ["Larsen & Toubro (L&T)", "Tata Projects", "CPWD / NHAI", "Bechtel", "AECOM"]
            score = 83
            expectation = "Designing iconic infrastructure, outdoor project freedom, and stable construction growth."
            unfiltered_reality = "Challenging onsite field conditions, strict structural safety accountability, weather delays, and site relocation management."
        elif any(w in n for w in ["doctor", "surgeon", "physician", "dentist", "anesthesiologist", "medical", "nurse", "pharmacist"]):
            sal = "₹12 - ₹35 Lakhs / yr" if country_clean == "India" else "$120,000 - $350,000 / yr"
            orgs = ["AIIMS / Major Govt Hospitals", "Apollo Hospitals", "Fortis Healthcare", "Max Healthcare", "Cipla & Sun Pharma"]
            score = 92
            expectation = "High medical respect, high starting income, and immediate clinical authority."
            unfiltered_reality = "Requires 5.5+ years MBBS + 3 years MD/MS residency, 60-80 hour work weeks during initial years, high emotional stamina, and lifelong clinical updates."
        elif any(w in n for w in ["farmer", "agronomist", "botanist", "agriculture", "soil", "crop", "farm"]):
            sal = "₹4 - ₹14 Lakhs / yr" if country_clean == "India" else "$45,000 - $95,000 / yr"
            orgs = ["ICAR Agricultural Institutes", "Ministry of Agriculture", "AgriTech Startups", "NABARD", "National Seeds Corporation"]
            score = 81
            expectation = "Outdoor independence, working with nature, and organic sustainable farming."
            unfiltered_reality = "High dependence on seasonal climate patterns, supply chain market fluctuations, capital intensive equipment, and physical labor."
        elif any(w in n for w in ["teacher", "professor", "lecturer", "educator", "tutor", "principal", "academic"]):
            sal = "₹4.5 - ₹16 Lakhs / yr" if country_clean == "India" else "$50,000 - $98,000 / yr"
            orgs = ["Central & State Universities", "NCERT / State School Boards", "IITs / NITs", "EdTech Enterprises", "International Academies"]
            score = 84
            expectation = "Structured working hours, long summer vacations, and high academic respect."
            unfiltered_reality = "Heavy administrative grading workload, managing diverse student learning paces, and requirement of NET/PhD for university tenure."
        elif any(w in n for w in ["lawyer", "attorney", "advocate", "judge", "solicitor", "paralegal"]):
            sal = "₹6 - ₹28 Lakhs / yr" if country_clean == "India" else "$85,000 - $190,000 / yr"
            orgs = ["Supreme & High Courts", "Corporate Law Firms", "AZB & Partners", "Shardul Amarchand Mangaldas", "Corporate Legal Departments"]
            score = 89
            expectation = "High courtroom drama, immediate high retainer fees, and rapid prestige."
            unfiltered_reality = "Long hours reading case law, initial low junior clerkship stipends, building client networks from scratch, and high stress court deadlines."
        elif any(w in n for w in ["pilot", "captain", "aviation", "aeronautical", "flight"]):
            sal = "₹15 - ₹48 Lakhs / yr" if country_clean == "India" else "$95,000 - $240,000 / yr"
            orgs = ["Air India", "IndiGo Airlines", "Emirates", "Boeing & Airbus", "Directorate General of Civil Aviation"]
            score = 91
            expectation = "Global luxury travel, high glamour, and high starting aviation pay."
            unfiltered_reality = "High Commercial Pilot License (CPL) training cost (₹40-50L+), strict biannual medical checks, irregular sleep cycles, and jet lag."
        elif any(w in n for w in ["chef", "cook", "baker", "culinary", "hotel"]):
            sal = "₹4.5 - ₹18 Lakhs / yr" if country_clean == "India" else "$42,000 - $95,000 / yr"
            orgs = ["Taj Hotels & Resorts", "Oberoi Group", "Marriott International", "Michelin Star Restaurants", "Luxury Cruise Lines"]
            score = 82
            expectation = "Creative food art, celebrity chef status, and culinary innovation."
            unfiltered_reality = "12+ hour standing kitchen shifts, intense weekend & holiday pressure, high kitchen temperatures, and strict hygiene compliance."
        elif any(w in n for w in ["engineer", "developer", "software", "data", "ai", "cloud"]):
            sal = "₹7 - ₹30 Lakhs / yr" if country_clean == "India" else "$80,000 - $180,000 / yr"
            orgs = ["Google", "Microsoft", "TCS / Infosys", "Amazon", "NVIDIA"]
            score = 93
            expectation = "High tech salaries, total remote flexibility, and rapid career growth."
            unfiltered_reality = "Frequent technical interview rounds, screening algorithm tests, 40-50 hour screen time, and constant rapid technology updates."
        else:
            sal = "₹5 - ₹18 Lakhs / yr" if country_clean == "India" else "$55,000 - $120,000 / yr"
            orgs = ["Leading Industry Enterprises", "Multinational Corporations", "Public Sector Undertakings", "Growth Startups"]
            score = 85
            expectation = "Stable corporate career, steady promotions, and professional growth."
            unfiltered_reality = "Requires continuous skill refinement, performance KPI tracking, and building verifiable domain proof of work."
            sal = "₹6 - ₹18 Lakhs / yr" if country_clean == "India" else "$60,000 - $130,000 / yr"
            orgs = ["Leading Industry Organizations", "Global Enterprise Corporations", "Specialized Research Institutes", "National Government Boards", "Top Sector Consultancies"]
            score = 85

        cities = [
            {"city": "New Delhi", "country": "India", "demand": "High", "companies": ["Govt Ministries", "Public Bodies"], "reason": "National administrative hub"},
            {"city": "Mumbai", "country": "India", "demand": "Very High", "companies": ["Corporate HQs", "Industry Leaders"], "reason": "Commercial capital of India"},
            {"city": "Bengaluru", "country": "India", "demand": "Very High", "companies": ["R&D Centers", "Innovation Hubs"], "reason": "Primary innovation city"},
            {"city": "Hyderabad", "country": "India", "demand": "High", "companies": ["Pharma & Sector Giants"], "reason": "Major industrial ecosystem"},
            {"city": "Pune", "country": "India", "demand": "High", "companies": ["Academic & Manufacturing Centers"], "reason": "Key educational & sector hub"}
        ] if country_clean == "India" else [
            {"city": "New York", "country": country_clean, "demand": "Very High", "companies": ["Global Leaders"], "reason": "International economic center"},
            {"city": "London", "country": country_clean, "demand": "Very High", "companies": ["Multinational Corps"], "reason": "Major global administrative center"},
            {"city": "San Francisco", "country": country_clean, "demand": "High", "companies": ["Innovation Pioneers"], "reason": "Technology & research hub"},
            {"city": "Tokyo", "country": country_clean, "demand": "High", "companies": ["Enterprise Giants"], "reason": "Leading Asian economic hub"},
            {"city": "Dubai", "country": country_clean, "demand": "High", "companies": ["Global Hubs"], "reason": "Middle East business capital"}
        ]

        return {
            "name": name,
            "salary": {
                "experience_level": "Fresher to Mid-Level",
                "country": country_clean,
                "amount": sal,
                "currency": curr_info,
                "reason": f"Compensation levels for a {name} reflect high cognitive demand, specialized technical expertise, and local talent scarcity."
            },
            "overall_score": score,
            "salary_score": min(100, max(50, score + 2)),
            "demand": "High Growth Demand",
            "demand_score": min(100, max(60, score - 3)),
            "growth": "Strong 5-Year Outlook",
            "growth_score": min(100, max(65, score + 1)),
            "learning_time": "3 - 5 Years Degree / Professional Training",
            "expectation": expectation,
            "unfiltered_reality": unfiltered_reality,
            "personality_fit": [
                f"Strong interest in {name} domain",
                "Analytical & Problem Solving Mindset",
                "Dedicated Continuous Learning Ability",
                "Effective Communication & Leadership Skills"
            ],
            "future_timeline": [
                "Entry Level (0-2 Yrs): Core Fundamentals & Specialized Training",
                "Mid Level (2-5 Yrs): Independent Execution & Project Leadership",
                "Senior Level (5+ Yrs): Strategic Management & Executive Expert"
            ],
            "risks": [
                "Initial competitive selection & qualification benchmarks",
                "Evolving sector regulations & modern workflow adoption",
                "Workload and project delivery demands during peak periods"
            ],
            "learning_path": [
                "Stage 1: Foundational Academic Degree or Professional Certification",
                "Stage 2: Practical Field Internships & Real-World Projects",
                "Stage 3: Advanced Domain Specialization & Senior Leadership"
            ],
            "organizations": orgs,
            "top_cities": cities
        }

    c1_data = get_role_data(career1)
    c2_data = get_role_data(career2)
    
    winner_name = career1 if c1_data["overall_score"] >= c2_data["overall_score"] else career2
    loser_name = career2 if winner_name == career1 else career1

    return {
        "career1": c1_data,
        "career2": c2_data,
        "winner": winner_name,
        "reason": f"{winner_name} demonstrates outstanding sector resilience, structured compensation progression, and expansive long-term career growth opportunities in {country_clean}.",
        "recommendation": f"If you seek strong career stability, high sector growth, and high impact opportunities, pursuing a career in {winner_name} is highly recommended. However, if your personal passion aligns with {loser_name}, both fields offer excellent professional development."
    }

INDIA_SPECIFIC_TERMS = ["upsc", "ias", "ips", "ssc", "gate", "nda", "cds", "mhcer", "mhcet", "mht cet", "mhtcet", "kcet", "k-cet", "keam", "eamcet", "wbjee", "ojee", "gujcet", "mpsc", "bpsc", "uppsc", "ras", "jee", "neet", "ifs", "irs", "ies", "cat", "clat", "ibps", "sbi po", "cgl", "chsl"]
USA_SPECIFIC_TERMS = ["usmle", "nclex", "bar exam", "sat", "act"]
UK_SPECIFIC_TERMS = ["plab", "gmc"]

def check_region_mismatch(c1, c2, country):
    country_lower = country.lower().strip() if country else ""
    c1_lower = c1.lower().strip()
    c2_lower = c2.lower().strip()
    
    warnings = []
    for c_term, c_name in [(c1_lower, c1), (c2_lower, c2)]:
        # Check India specific exams
        if any(term in c_term.split() or term == c_term or term in c_term for term in INDIA_SPECIFIC_TERMS):
            if country_lower and country_lower not in ["india", "in", "bharat"]:
                warnings.append(f"⚠️ <strong>Region-Specific Career Alert for {c_name.upper()}:</strong> {c_name.upper()} is an official state/national entrance examination conducted in <strong>India</strong> (e.g. Maharashtra MHT-CET, Karnataka KCET, UPSC, JEE, NEET). It does not exist as an exam in <strong>{country.title()}</strong>. The salary compensation for {c_name.upper()} is displayed in <strong>Indian Rupees (₹)</strong>, while global career roles are shown in local {country.title()} currency.")
        # Check USA specific exams
        elif any(term in c_term.split() or term == c_term or term in c_term for term in USA_SPECIFIC_TERMS):
            if country_lower and country_lower not in ["usa", "united states", "us", "america"]:
                warnings.append(f"⚠️ <strong>Region-Specific Career Alert for {c_name.upper()}:</strong> {c_name.upper()} is a US-specific national credential/exam conducted in the <strong>United States</strong>. It is not an official examination in <strong>{country.title()}</strong>.")
    
    return " <br><br> ".join(warnings) if warnings else None

@app.route("/compare-api", methods=["POST"])
def compare_api():
    try:
        data = request.get_json() or {}

        career1_raw = data.get("career1", "").strip()
        career2_raw = data.get("career2", "").strip()
        country_raw = data.get("country", "").strip()

        is_v1, err1 = validate_career_input(career1_raw)
        if not is_v1:
            return failure(f"Career 1 Error: {err1}", 400)

        is_v2, err2 = validate_career_input(career2_raw)
        if not is_v2:
            return failure(f"Career 2 Error: {err2}", 400)

        if country_raw:
            is_vc, country_err = validate_country_strict(country_raw)
            if not is_vc:
                return failure(country_err, 400)
            country = country_err
        else:
            country = "India"

        career1 = err1
        career2 = err2
        currency = COUNTRY_CURRENCY.get(country.title(), "Detect official currency")

        if not career1 or not career2:
            return failure("Please enter both careers.", 400)

        prompt = f"""
You are CareerVerse AI.

Compare these two careers professionally.

Career 1:
{career1}

Career 2:
{career2}

Student Selected Country:
{country if country else "Not Provided"}

Selected Country Currency:
{currency}

CRITICAL LOCATION VALIDATION INSTRUCTION:
Check if Career 1 or Career 2 is a nation-specific exam, civil service, or national credential (e.g., UPSC, IAS, IPS, SSC, GATE, NDA, MPSC, USMLE, NCLEX, PLAB, Bar Exam).
If the user's selected country does NOT conduct or recognize this exam/role natively (for example, UPSC in USA or USMLE in India):
In "country_mismatch_warning", provide a bold clear statement explaining the geographic restriction (e.g., "⚠️ Region-Specific Career Alert: UPSC (Union Public Service Commission) is an Indian Civil Services examination for government administration in India. It is not an exam conducted in USA. The equivalent US career pathway is US Federal Civil Service / Foreign Service.").

Return ONLY valid JSON.

JSON Format:
{{
"country_mismatch_warning": "",
"career1": {{
"name": "",
"salary": {{
"experience_level": "Fresher",
"country": "",
"amount": "",
"currency": "",
"reason": "Detailed explanation explaining why this career commands this salary (e.g. key drivers like talent scarcity, cognitive demand, credentials, industry margins, etc.)"
}},
"overall_score": 0,
"salary_score": 0,
"demand": "",
"demand_score": 0,
"growth": "",
"growth_score": 0,
"learning_time": "",
"ai_automation_risk": "Low (15%) - High Analytical Complexity",
"work_life_balance": "40-45 Hours/Week - Hybrid Remote",
"education_roi_years": "1-2 Years Post Graduation",
"expectation": "High starting pay, minimal overtime, and immediate remote flexibility.",
"unfiltered_reality": "Requires 3-4 years of rigorous preparation, initial entry-level hustle, tight deadlines, and constant upskilling.",
"personality_fit": [],
"future_timeline": [],
"risks": [],
"learning_path": [],
"organizations": [],
"top_cities": []
}},
"career2": {{
"name": "",
"salary": {{
"experience_level": "Fresher",
"country": "",
"amount": "",
"currency": "",
"reason": "Detailed explanation explaining why this career commands this salary..."
}},
"overall_score": 0,
"salary_score": 0,
"demand": "",
"demand_score": 0,
"growth": "",
"growth_score": 0,
"learning_time": "",
"ai_automation_risk": "Low (20%) - Core Domain Expertise Needed",
"work_life_balance": "40-45 Hours/Week - Office & Field",
"education_roi_years": "1-2 Years Post Graduation",
"expectation": "Easy entry barrier, quick promotions, and low technical demands.",
"unfiltered_reality": "Requires high domain accountability, handling complex stakeholder demands, and building proven domain projects.",
"personality_fit": [],
"future_timeline": [],
"risks": [],
"learning_path": [],
"organizations": [],
"top_cities": []
}},
"winner": "",
"reason": "",
"recommendation": ""
}}
"""
        try:
            text = generate_with_fallback(prompt)
            text = clean_json(text)
            result = json.loads(text)
            if not isinstance(result, dict) or "career1" not in result or "career2" not in result:
                raise ValueError("Incomplete JSON structure from AI model")
        except Exception as e:
            print(f"[COMPARE FALLBACK ENGAGED] {e}. Generating dynamic fallback comparison for {career1} vs {career2}")
            result = generate_fallback_compare(career1, career2, country)

        # Attach deterministic region mismatch alert if applicable
        mismatch_alert = check_region_mismatch(career1, career2, country)
        if mismatch_alert:
            result["country_mismatch_warning"] = mismatch_alert
        elif not result.get("country_mismatch_warning"):
            result["country_mismatch_warning"] = ""

        if not result.get("winner"):
            c1_s = result.get("career1", {}).get("overall_score", 85)
            c2_s = result.get("career2", {}).get("overall_score", 80)
            result["winner"] = career1 if c1_s >= c2_s else career2

        # Normalize top_cities & attach ground-truth normalized salary benchmark engine
        for c_key in ["career1", "career2"]:
            if c_key in result and isinstance(result[c_key], dict):
                c_name = result[c_key].get("name", career1 if c_key == "career1" else career2)
                norm_sal = create_normalized_salary_object(c_name, country)
                llm_sal = result[c_key].get("salary")
                if isinstance(llm_sal, dict) and llm_sal.get("reason"):
                    norm_sal["reason"] = llm_sal.get("reason")
                result[c_key]["salary_benchmark"] = norm_sal

                cities_raw = result[c_key].get("top_cities", [])
                normalized_cities = []
                for item in cities_raw:
                    if isinstance(item, str):
                        normalized_cities.append({
                            "city": item,
                            "country": country,
                            "demand": "High Demand",
                            "companies": ["Major Sector Employers"],
                            "reason": f"Key opportunity hub in {country}"
                        })
                    elif isinstance(item, dict):
                        normalized_cities.append(item)
                result[c_key]["top_cities"] = normalized_cities

        return success(result)

    except Exception as e:
        print(f"Compare API Error: {e}")
        return failure("Unable to compare careers. Please try again.")


    except json.JSONDecodeError:

        traceback.print_exc()

        return failure(
            "Gemini returned invalid JSON."
        )


    except Exception as e:

        traceback.print_exc()

        return handle_gemini_error(e)
# =====================================================
# Resume Analyzer API (Protected by Secure Processing Layer)
# =====================================================

@app.route("/resume-api", methods=["POST"])
@rate_limit_sensitive
def resume_api():
    try:
        if "resume" not in request.files:
            return failure("Please upload a resume.", 400)

        file = request.files["resume"]

        if file.filename == "":
            return failure("No file selected.", 400)

        if not allowed_file(file.filename):
            return failure("Invalid file type. Only PDF files are allowed.", 400)

        # 1. Zero Disk Retention: In-memory stream processing with validation
        pdf_bytes = file.read()
        file_stream = io.BytesIO(pdf_bytes)

        is_valid_pdf, val_err = validate_pdf_stream(file_stream, max_size_bytes=10 * 1024 * 1024)
        if not is_valid_pdf:
            audit_logger.log_event("INVALID_PDF_UPLOAD_REJECTED", "BLOCKED", details={"error": val_err}, level=30)
            return failure(val_err, 400)

        resume_text = ""
        try:
            with pdfplumber.open(file_stream) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        resume_text += text + "\n"
        except Exception as pdf_err:
            audit_logger.log_event("PDF_EXTRACTION_ERROR", "FAILURE", details={"error": str(pdf_err)}, level=30)
            return failure("Unable to read the uploaded resume or the file is corrupted.", 400)
        finally:
            file_stream.close()

        if resume_text.strip() == "":
            return failure("Unable to read any text from the uploaded resume.", 400)

        target_role = request.form.get("target_role", "").strip()
        if target_role:
            is_v_r, role_err = validate_career_input(target_role)
            if not is_v_r:
                return failure(role_err, 400)

        # 2. Secure Processing Layer: PII Minimization and Redaction inside Secure Enclave
        sec_res = process_sensitive_data(resume_text, options={"target_role": target_role})
        sanitized_resume_text = sec_res["processed_text"]

        prompt = f"""
You are a Senior FAANG Executive Recruiter, ATS Optimization Specialist, and Technical Hiring Manager.

EVALUATION TASK:
Analyze the candidate's resume text and perform a hyper-rigorous, accurate ATS evaluation specifically for the Target Job Role: "{target_role if target_role else 'General Role'}".

Candidate Resume Content (PII-Minimally De-identified):
{sanitized_resume_text}

CRITICAL ACCURACY INSTRUCTIONS:
1. ATS Compatibility Score (ats_score): Measure exact keyword match, section formatting, and skill alignment for "{target_role if target_role else 'General Role'}". If key industry tools/keywords for "{target_role if target_role else 'General Role'}" are missing, penalize the score accurately.
2. Job Readiness Score (job_readiness_score): Evaluate real projects, internships, domain skills, and technical depth.
3. Recruiter Impact Score (recruiter_impact_score): Evaluate layout clarity, professional summary quality, and metric-driven bullet points.
4. Skill Evidence Score (skill_evidence_score): Check for quantifiable metrics (percentages, speed gains, user counts, code links, live project URLs).
5. Interview Confidence Score (interview_confidence_score): Determine if the resume projects sufficient technical depth to survive rigorous technical interview questioning for "{target_role if target_role else 'General Role'}".

Return ONLY valid JSON in this exact structure:

{{
  "target_role": "{target_role if target_role else 'General Role'}",
  "ats_score": 0,
  "job_readiness_score": 0,
  "recruiter_impact_score": 0,
  "skill_evidence_score": 0,
  "interview_confidence_score": 0,
  "quantified_metrics_score": 0,
  "google_xyz_compliance": "High / Medium / Low",
  "ats_pass_status": "High ATS Pass Probability",
  "experience_level": "Mid-Level",
  "recommended_roles": ["Role 1", "Role 2", "Role 3", "Role 4", "Role 5"],
  "strengths": ["Strength 1", "Strength 2", "Strength 3", "Strength 4", "Strength 5"],
  "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3", "Weakness 4", "Weakness 5"],
  "missing_skills": ["Missing Skill 1", "Missing Skill 2", "Missing Skill 3", "Missing Skill 4", "Missing Skill 5"],
  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3", "Suggestion 4", "Suggestion 5"],
  "final_verdict": "Detailed professional recruiter verdict statement..."
}}

Scoring & Format Rules:
- All scores (ats_score, job_readiness_score, recruiter_impact_score, skill_evidence_score, interview_confidence_score) MUST be realistic numbers between 0 and 100.
- ats_pass_status must be one of: "High ATS Pass Probability" (if ats_score >= 75), "Moderate ATS Compatibility" (if 55-74), or "ATS Revision Recommended" (if < 55).
- Do NOT inflate scores; base every point on explicit evidence in the resume text.
- recommended_roles, strengths, weaknesses, missing_skills, and suggestions must contain exactly 5 actionable items each.
- Return ONLY valid JSON. No markdown fences.
"""

        text = generate_with_fallback(prompt)
        text = clean_json(text)

        try:
            result = json.loads(text)
        except Exception:
            audit_logger.log_event("AI_INVALID_JSON_RESPONSE", "FAILURE", level=30)
            return failure("AI returned invalid JSON. Try again.")

        # Attach authentic, verified security metadata
        sec_status = get_security_status()
        result["security"] = {
            "mode": sec_res["security_metadata"]["mode"],
            "hardware_isolated": sec_res["security_metadata"]["hardware_isolated"],
            "display_badge": sec_status["display_badge"],
            "badge_color": sec_status["badge_color"],
            "pii_entities_redacted": sec_res["redacted_entities_count"],
            "redacted_types": sec_res["redacted_types"],
            "entities_breakdown": sec_res["entities_breakdown"],
            "zero_disk_retention": True
        }

        audit_logger.log_event(
            event_type="RESUME_EVALUATION_COMPLETED",
            status="SUCCESS",
            details={
                "target_role": target_role or "General Role",
                "pii_redacted_count": sec_res["redacted_entities_count"],
                "hardware_isolated": sec_res["security_metadata"]["hardware_isolated"]
            }
        )

        return success(result)

    except json.JSONDecodeError:
        traceback.print_exc()
        return failure("Gemini returned invalid JSON.")

    except Exception as e:
        traceback.print_exc()
        return handle_gemini_error(e)


# =====================================================
# Security & Confidential Computing Diagnostics API
# =====================================================

@app.route("/api/security-status", methods=["GET"])
def security_status_api():
    """Returns honest, verifiable security status of the running instance."""
    status = get_security_status()
    return jsonify({
        "success": True,
        "security": status
    })


@app.route("/api/security-attestation", methods=["GET", "POST"])
def security_attestation_api():
    """Returns cryptographic attestation report from TEE provider or simulation diagnostic."""
    nonce = request.args.get("nonce")
    if not nonce and request.is_json:
        nonce = request.json.get("nonce")
    nonce_bytes = nonce.encode("utf-8") if nonce else None
    report = get_attestation_report(nonce_bytes)
    return jsonify({
        "success": True,
        "attestation": report
    })

# =====================================================
# Career Reality AI API
# =====================================================

# =====================================================
# Career Reality AI API & Fallback
# =====================================================

def get_fallback_career_reality(career, country):
    c_title = career.title() if career else "Target Career"
    is_india = (country or "").lower().find("india") != -1 or country == "Global" or not country
    
    is_medical = any(x in c_title.lower() for x in ["neet", "medical", "doctor", "mbbs", "physician", "health", "nursing", "clinic"])
    
    if is_medical:
        return {
            "career": "NEET / Medical & Healthcare Specialist",
            "country": country or "Global",
            "reality_score": 92,
            "reality_status": "High Prestige & Critical Human Service Career with Intense Initial Preparation",
            "stress_level": "High Workload & Residency Stress (Requires High Emotional Resilience)",
            "daily_work": [
                "Clinical patient rounds, consultations, and diagnostic assessments.",
                "Reviewing lab reports, medical histories, and prescribing treatment protocols.",
                "High-intensity shift duties, emergency triage, and surgical or procedural care.",
                "Continuous medical study, research updates, and regulatory compliance.",
                "Communicating empathetic diagnoses to patients and coordinating care with specialists."
            ],
            "hidden_truths": [
                "Clearing NEET/MBBS requires 5-8+ years of relentless study and post-grad specialization.",
                "Initial residency years involve long 24-36 hour shifts and intense emotional stamina.",
                "Financial returns peak after specialization (MD/MS), leading to exceptional lifetime job security.",
                "Work-life balance stabilizes significantly once you establish private practice or senior consultancy.",
                "Empathy and diagnostic intuition are 100% irreplaceable by AI or automation."
            ],
            "technical_difficulty": 88,
            "competition_level": 95,
            "learning_difficulty": 90,
            "salary_reality": f"High lifetime earning potential in {country or 'India'}, with rapid acceleration post-specialization.",
            "fresher_salary": "₹6.5L - ₹12.0L / yr (Resident Intern)" if is_india else "$75,000 - $110,000 / yr",
            "mid_salary": "₹18.0L - ₹35.0L / yr (Medical Officer / MD)" if is_india else "$160,000 - $240,000 / yr",
            "senior_salary": "₹40.0L - ₹1.2Cr+ / yr (Senior Consultant / Surgeon)" if is_india else "$280,000 - $550,000+ / yr",
            "not_for_you": [
                "You want quick 6-month shortcuts to high income without long study commitments.",
                "You struggle with high-pressure environments, long hospital shifts, or emergency calls.",
                "You prefer purely solitary desk jobs without direct patient interactions."
            ],
            "expectation_vs_reality": {
                "expectation": "Immediate high earnings, relaxed hospital shifts, and low competitive pressure.",
                "unfiltered_reality": "Requires 5-8+ years of relentless study (NEET/MBBS/MD), managing intense 24-36 hour residency shifts, and high emotional resilience.",
                "success_key": "Master clinical fundamentals, develop high stress tolerance, and commit to long-term patient care dedication."
            },
            "industry_reality": "The medical profession is globally recession-proof with 100% long-term job security and immense societal impact.",
            "ai_verdict": "Zero AI Disruption Risk: Human empathy, physical diagnostics, and surgical precision remain 100% human-driven."
        }

    sal_bench = get_career_salary_benchmark(career, country)
    fresher_sal = sal_bench["fresher"]
    mid_sal = sal_bench["mid"]
    senior_sal = sal_bench["senior"]

    return {
        "career": c_title,
        "country": country or "Global",
        "reality_score": 86,
        "reality_status": f"High Growth & Rewarding Professional Path for {c_title}",
        "stress_level": "Moderate to High (Demanding Workload & Technical Accuracy Needed)",
        "daily_work": [
            f"Core technical and operational execution in line with {c_title} standards.",
            "Cross-functional collaboration with stakeholders and team members.",
            "Continuous problem solving, troubleshooting, and quality verification.",
            "Documentation, reporting, and process compliance management.",
            "Skill upskilling and adapting to new technology / industry protocols."
        ],
        "hidden_truths": [
            "Continuous learning and skill updating is mandatory to stay competitive.",
            "Initial entry-level roles require high grit, practice, and patience.",
            "Soft skills and communication are as critical as technical proficiency.",
            "Workplace expectations require managing tight deadlines and priorities.",
            "Building a strong personal portfolio or track record opens elite offers."
        ],
        "technical_difficulty": 78,
        "competition_level": 82,
        "learning_difficulty": 75,
        "salary_reality": f"Competitive compensation structure reflecting market demand for {c_title} in {country or 'Global'}.",
        "fresher_salary": fresher_sal,
        "mid_salary": mid_sal,
        "senior_salary": senior_sal,
        "not_for_you": [
            "You prefer repetitive tasks without continuous learning.",
            "You dislike adapting to shifting industry tools and requirements.",
            "You expect immediate high rewards without initial dedicated practice."
        ],
        "expectation_vs_reality": {
            "expectation": "Immediate high salary, minimal overtime, and effortless job stability from Day 1.",
            "unfiltered_reality": f"Initial 3-5 years require high grit, continuous self-study, managing tight deadlines, and proving value before reaching top pay.",
            "success_key": "Build a strong portfolio of work, maintain emotional stamina under pressure, and commit to 100% continuous upskilling."
        },
        "industry_reality": f"The {c_title} industry is rapidly evolving with high long-term career growth, rewarding dedicated practitioners with high impact and competitive compensation.",
        "ai_verdict": f"{c_title} remains a top-tier career choice with strong long-term market sustainability."
    }

@app.route("/career-reality-api", methods=["POST"])
def career_reality_api():
    try:
        data = request.get_json() or {}
        career = data.get("career","").strip()
        
        if not career:
            return failure("Please enter a target career title.", 400)
            
        is_v_c, career_err = validate_career_input(career)
        if not is_v_c:
            # Fallback if user types exam/slash combinations
            if any(x in career.lower() for x in ["neet", "medical", "doctor", "jee", "upsc", "gate", "cat"]):
                return success(get_fallback_career_reality(career, data.get("country", "")))
            return failure(career_err, 400)

        country_raw = data.get("country", "").strip()
        if country_raw:
            is_v_cntry, country_err = validate_country_strict(country_raw)
            if not is_v_cntry:
                country = "Global"
            else:
                country = country_err
        else:
            country = "Global"

        prompt = f"""
You are CareerVerse AI Career Reality Expert.

CRITICAL INITIAL CHECK:
Is "{career}" a real, recognizable job role, medical/engineering entrance path, or profession (such as Software Engineer, AI Engineer, Data Scientist, Doctor, NEET / Medical Candidate, Nurse, Accountant, Lawyer, Teacher, Engineer, etc.)?
If "{career}" is random gibberish or nonsensical text (like "uwgyue", "jhdbeg", "asdf123", "12345"), return ONLY this JSON:
{{
  "error": "Invalid Career Name: '{career}' is not a recognized job role or career path."
}}

Otherwise, analyze the real-world truth of this career / study path.
If "{career}" mentions NEET, Medical, Doctor, or Healthcare, provide authentic medical industry realities, clinical workloads, residency stress, and realistic medical compensation for {country}.

Career:
{career}

Country:
{country}

Return ONLY valid JSON.

Format:
{{
  "reality_score": 88,
  "reality_status": "High Growth & Rewarding Professional Path",
  "stress_level": "Moderate to High",
  "daily_work": ["Duty 1", "Duty 2", "Duty 3", "Duty 4", "Duty 5"],
  "hidden_truths": ["Truth 1", "Truth 2", "Truth 3", "Truth 4", "Truth 5"],
  "technical_difficulty": 80,
  "competition_level": 85,
  "learning_difficulty": 78,
  "salary_reality": "Realistic salary breakdown for {country}.",
  "fresher_salary": "<fresher_salary_range>",
  "mid_salary": "<mid_salary_range>",
  "senior_salary": "<senior_salary_range>",
  "not_for_you": ["Reason 1", "Reason 2", "Reason 3"],
  "industry_reality": "Unfiltered market truth.",
  "ai_verdict": "Long-term AI impact assessment."
}}

Rules:
- STRICT FACT-CHECKED MARKET STATISTICS MANDATE: All salary ranges, reality scores, competition levels, and technical difficulty scores MUST be 100% accurate, realistic, and grounded in real-world market benchmarks (Glassdoor, Payscale, Levels.fyi, NASSCOM, BLS) for {country} and {career}.
- reality_score between 0-100.
- technical_difficulty between 0-100.
- competition_level between 0-100.
- learning_difficulty between 0-100.
- daily_work exactly 5 points.
- hidden_truths exactly 5 points.
- not_for_you exactly 3 points.
- fresher_salary, mid_salary, senior_salary must be accurate, non-empty salary ranges for {country} with local currency.
- Return only JSON.
"""

        try:
            text = generate_with_fallback(prompt)
            text = clean_json(text)
            result = json.loads(text)
            if "error" in result or result.get("error"):
                return success(get_fallback_career_reality(career, country))
            return success(result)
        except Exception as err_api:
            traceback.print_exc()
            return success(get_fallback_career_reality(career, country))

    except Exception as e:
        traceback.print_exc()
        return success(get_fallback_career_reality("Target Career", "Global"))
    

# =====================================================
# Career Intelligence Dashboard API
# =====================================================

@app.route("/career-intelligence-api", methods=["POST"])
def career_intelligence_api():

    try:

        data = request.get_json()

        career = data.get("career", "").strip()
        is_v, err = validate_career_input(career)
        if not is_v:
            return failure(err, 400)
        country_raw = data.get("country", "").strip()
        if country_raw:
            is_v_c, country_err = validate_country_strict(country_raw)
            if not is_v_c:
                return failure(country_err, 400)
            country = country_err
        else:
            country = "Global"

        if career == "":
            return failure("Please enter a career.", 400)

        current_year = datetime.now().year

        years = [
            current_year - 3,
            current_year - 2,
            current_year - 1,
            current_year,
            current_year + 1,
            current_year + 2,
            current_year + 3,
            current_year + 4,
            current_year + 5
        ]

        prompt = f"""
You are CareerVerse AI.
You are an expert Career Intelligence Analyst.

CRITICAL INITIAL CHECK:
Is "{career}" a real, recognizable job role or profession (such as Software Engineer, AI Engineer, Data Scientist, Doctor, Accountant, Graphic Designer, Lawyer, Teacher, Environmental Engineer, etc.)?
If "{career}" is NOT a real job role or profession (for example if it is random letters like "uwgyue", "jhdbeg", "asdf", numbers like "1234", or nonsensical text), you MUST return ONLY this JSON:
{{
  "error": "Invalid Career Name: '{career}' is not a recognized job role. Please enter a valid career title (e.g. Software Engineer, Data Scientist)."
}}

Otherwise, analyze ONLY the selected career.

Career:
{career}

Country:
{country if country else "Global"}

Current Year:
{current_year}

Timeline

Past:
{years[0]}, {years[1]}, {years[2]}

Present:
{years[3]}

Future:
{years[4]}, {years[5]}, {years[6]}, {years[7]}, {years[8]}

IMPORTANT RULES

- Never assume every career is related to programming.
- Analyse only the selected profession.
- Use realistic industry trends.
- Base the analysis on the selected country whenever possible.
- Past values should reflect historical trends.
- Present values should reflect the current market.
- Future values should be realistic predictions.
- Explain WHY every trend changes.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not write explanations outside JSON.

Return this JSON exactly:

{{
  "career":"",

  "summary":{{
    "overview":"",
    "difficulty":"",
    "education":"",
    "average_salary":"",
    "fresher_salary":"",
    "mid_salary":"",
    "senior_salary":"",
    "future_rating":0,
    "confidence":0
  }},

  "charts":{{

    "career_demand":{{
      "labels":{years},
      "values":[0,0,0,0,0,0,0,0,0],
      "reason":""
    }},

    "salary_growth":{{
      "labels":[
        "Student",
        "Intern",
        "Entry",
        "Junior",
        "Mid",
        "Senior",
        "Expert"
      ],
      "values":[0,0,0,0,0,0,0],
      "reason":""
    }},

    "competition":{{
      "labels":{years},
      "values":[0,0,0,0,0,0,0,0,0],
      "reason":""
    }},

    "technology":{{
      "labels":[
        "Past",
        "Present",
        "Future"
      ],
      "values":[0,0,0],
      "reason":""
    }},

    "automation":{{
      "score":0,
      "reason":""
    }},

    "skills":{{
      "technical":0,
      "communication":0,
      "leadership":0,
      "management":0,
      "problem_solving":0,
      "reason":""
    }},

    "global_demand":{{
      "countries":[],
      "values":[],
      "reason":""
    }}

  }},

  "career_path":[],

  "future_opportunities":[],

  "top_companies":[],

  "recommended_tools":[],

  "certifications":[],

  "ai_advice":[]

}}

Rules:

- confidence must be between 80 and 100.
- future_rating must be between 0 and 100.
- fresher_salary must be the realistic entry/fresher level compensation for {career} in {country} (e.g., '₹5L - ₹8L / yr' or '$70k - $90k / yr').
- mid_salary must be the realistic mid-level compensation (3-6 yrs) for {career} in {country} (e.g., '₹12L - ₹20L / yr' or '$110k - $150k / yr').
- senior_salary must be the realistic experienced/senior compensation (7+ yrs) for {career} in {country} (e.g., '₹25L - ₹45L / yr' or '$160k - $240k / yr').
- salary_growth.values must contain actual numeric compensation figures (NOT percentages). For India, return values in Lakhs/yr (e.g., [0, 3, 7, 12, 18, 30, 48]). For USD/Global, return values in $k/yr (e.g., [0, 25, 75, 105, 145, 195, 260]).
- Every chart must contain realistic values.
- career_path must contain exactly 5 stages.
- future_opportunities must contain exactly 5 points.
- top_companies must contain exactly 5 companies.
- recommended_tools must contain exactly 5 tools.
- certifications must contain exactly 5 certifications.
- ai_advice must contain exactly 5 personalised suggestions.
- Return ONLY valid JSON.
"""
        text = generate_with_fallback(prompt)

        text = clean_json(text)

        result = json.loads(text)

        if "error" in result or result.get("error"):
            return failure(result["error"], 400)

        # -------------------------------
        # Default Structure & Smart Fallbacks
        # -------------------------------

        result.setdefault("career", career)

        summary = result.setdefault("summary", {})
        summary.setdefault("overview", "")
        summary.setdefault("difficulty", "")
        summary.setdefault("education", "")
        summary.setdefault("average_salary", "")
        summary.setdefault("future_rating", 75)
        summary.setdefault("confidence", 90)

        # Strict overwrite from verified database layer (Section 1)
        from salary_data_layer import get_verified_salary_data
        verified_res = get_verified_salary_data(career, country)
        
        if verified_res.get("salary") and (verified_res["salary"].get("min") or verified_res["salary"].get("fresher")):
            v_sal = verified_res["salary"]
            f_sal = v_sal.get("fresher") or v_sal.get("min")
            m_sal = v_sal.get("mid") or v_sal.get("median")
            s_sal = v_sal.get("senior") or v_sal.get("max")
            
            currency_symbol = verified_res.get("currency", {}).get("symbol", "$")
            def format_val(val):
                if val is None or val == "":
                    return ""
                if isinstance(val, (int, float)):
                    if verified_res.get("currency", {}).get("code") == "INR":
                        return f"₹{val/100000:.1f}L / yr"
                    return f"{currency_symbol}{val:,} / yr"
                return str(val)
                
            summary["fresher_salary"] = format_val(f_sal)
            summary["mid_salary"] = format_val(m_sal)
            summary["senior_salary"] = format_val(s_sal)
            summary["average_salary"] = format_val(m_sal)
        else:
            is_india = "india" in country.lower()
            summary["fresher_salary"] = "₹5.0L - ₹9.0L / yr" if is_india else "$65,000 - $85,000 / yr"
            summary["mid_salary"] = "₹12.0L - ₹20.0L / yr" if is_india else "$105,000 - $145,000 / yr"
            summary["senior_salary"] = "₹24.0L - ₹45.0L / yr" if is_india else "$155,000 - $240,000 / yr"
            summary["average_salary"] = summary["mid_salary"]


        charts = result.setdefault("charts", {})

        charts.setdefault("career_demand", {
            "labels": years,
            "values": [70] * 9,
            "reason": ""
        })

        charts.setdefault("salary_growth", {
            "labels": [
                "Student",
                "Intern",
                "Entry",
                "Junior",
                "Mid",
                "Senior",
                "Expert"
            ],
            "values": [0, 15, 35, 55, 75, 90, 100],
            "reason": ""
        })

        charts.setdefault("competition", {
            "labels": years,
            "values": [60] * 9,
            "reason": ""
        })

        charts.setdefault("technology", {
            "labels": ["Past", "Present", "Future"],
            "values": [40, 70, 95],
            "reason": ""
        })

        charts.setdefault("automation", {
            "score": 35,
            "reason": ""
        })

        charts.setdefault("skills", {
            "technical": 80,
            "communication": 75,
            "leadership": 60,
            "management": 55,
            "problem_solving": 90,
            "reason": ""
        })

        charts.setdefault("global_demand", {
            "countries": [],
            "values": [],
            "reason": ""
        })

        result.setdefault("career_path", [])
        result.setdefault("future_opportunities", [])
        result.setdefault("top_companies", [])
        result.setdefault("recommended_tools", [])
        result.setdefault("certifications", [])
        result.setdefault("ai_advice", [])

        return success(result)

    except json.JSONDecodeError:

        traceback.print_exc()

        return failure(
            "Gemini returned invalid JSON. Please try again."
        )

    except Exception as e:

        traceback.print_exc()

        return handle_gemini_error(e)        
# =====================================================
# Cost of Living & PPP Calculator API
# =====================================================

# Exchange rates (relative to 1 USD) and PPP Conversion Factors (relative to 1 USD)
# Source: World Bank / IMF / OECD / central banks 2024-2026 data
ECONOMIC_DATA = {
    "united states": {"exchange_rate": 1.0, "ppp_factor": 1.0, "col_index": 100.0},
    "india": {"exchange_rate": 83.5, "ppp_factor": 23.5, "col_index": 24.5},
    "united kingdom": {"exchange_rate": 0.78, "ppp_factor": 0.69, "col_index": 68.5},
    "canada": {"exchange_rate": 1.37, "ppp_factor": 1.21, "col_index": 67.2},
    "germany": {"exchange_rate": 0.92, "ppp_factor": 0.76, "col_index": 65.8},
    "france": {"exchange_rate": 0.92, "ppp_factor": 0.72, "col_index": 64.2},
    "australia": {"exchange_rate": 1.50, "ppp_factor": 1.42, "col_index": 77.4},
    "japan": {"exchange_rate": 155.0, "ppp_factor": 90.5, "col_index": 52.6},
    "singapore": {"exchange_rate": 1.34, "ppp_factor": 0.88, "col_index": 85.2},
    "brazil": {"exchange_rate": 5.15, "ppp_factor": 2.50, "col_index": 32.1},
    "south africa": {"exchange_rate": 18.2, "ppp_factor": 7.20, "col_index": 38.4},
    "united arab emirates": {"exchange_rate": 3.67, "ppp_factor": 2.15, "col_index": 59.5},
    "saudi arabia": {"exchange_rate": 3.75, "ppp_factor": 1.85, "col_index": 48.2},
    "switzerland": {"exchange_rate": 0.90, "ppp_factor": 1.12, "col_index": 118.5},
    "netherlands": {"exchange_rate": 0.92, "ppp_factor": 0.78, "col_index": 69.8},
    "ireland": {"exchange_rate": 0.92, "ppp_factor": 0.82, "col_index": 75.6},
    "china": {"exchange_rate": 7.25, "ppp_factor": 4.18, "col_index": 38.5},
    "russia": {"exchange_rate": 90.0, "ppp_factor": 30.2, "col_index": 31.8},
    "turkey": {"exchange_rate": 32.5, "ppp_factor": 9.50, "col_index": 34.2},
    "south korea": {"exchange_rate": 1360.0, "ppp_factor": 850.0, "col_index": 62.4},
    "new zealand": {"exchange_rate": 1.63, "ppp_factor": 1.48, "col_index": 71.5},
    "sweden": {"exchange_rate": 10.7, "ppp_factor": 8.80, "col_index": 63.8},
    "norway": {"exchange_rate": 10.8, "ppp_factor": 9.20, "col_index": 79.4},
    "denmark": {"exchange_rate": 6.9, "ppp_factor": 7.10, "col_index": 78.2},
    "hong kong": {"exchange_rate": 7.8, "ppp_factor": 6.05, "col_index": 76.5}
}

def get_country_currency_code_symbol(country):
    symbol_str = COUNTRY_CURRENCY.get(country.title(), "USD $")
    code, symbol = "USD", "$"
    parts = symbol_str.split()
    if len(parts) >= 2:
        code = parts[0]
        symbol = parts[1]
    elif len(parts) == 1:
        code = parts[0]
        symbol = ""
    return {"currency_code": code, "currency_symbol": symbol}

def get_country_col_info(country):
    clean_country = country.strip().lower()
    
    # Try alias resolve from COUNTRY_ALIAS_MAP in salary_data_layer
    try:
        from salary_data_layer import COUNTRY_ALIAS_MAP
        resolved_country = COUNTRY_ALIAS_MAP.get(clean_country, clean_country)
    except Exception:
        resolved_country = clean_country

    # Find matching record in ECONOMIC_DATA
    for name, info in ECONOMIC_DATA.items():
        if resolved_country == name or resolved_country in name:
            meta = get_country_currency_code_symbol(country)
            return {
                "index": info["col_index"],
                "exchange_rate": info["exchange_rate"],
                "ppp_factor": info["ppp_factor"],
                "currency_code": meta["currency_code"],
                "currency_symbol": meta["currency_symbol"]
            }
            
    # Fallback default values
    meta = get_country_currency_code_symbol(country)
    return {
        "index": 45.0,
        "exchange_rate": None,
        "ppp_factor": None,
        "currency_code": meta["currency_code"],
        "currency_symbol": meta["currency_symbol"]
    }

@app.route("/col-calculator")
def col_calculator():
    return render_template("col_calculator.html")

@app.route("/col-calculator-api", methods=["POST"])
def col_calculator_api():
    try:
        data = request.get_json() or {}
        base_salary_raw = data.get("base_salary", "")
        base_country = data.get("base_country", "").strip() or "United States"
        target_country = data.get("target_country", "").strip() or "India"
        career = data.get("career", "").strip() or "General"
        experience = data.get("experience", "").strip() or "Mid Level"
        target_city = data.get("target_city", "").strip() or ""

        # Validate inputs
        if not base_salary_raw:
            return failure("Please enter a base salary.", 400)
            
        try:
            base_salary = float(str(base_salary_raw).replace(",", "").replace("$", "").replace("₹", "").strip())
            if base_salary <= 0:
                return failure("Please enter a positive salary amount.", 400)
        except ValueError:
            return failure("Please enter a valid numeric salary.", 400)

        # Validate countries
        is_v_base, base_c_res = validate_country_strict(base_country)
        if not is_v_base:
            return failure(base_c_res, 400)
            
        is_v_target, target_c_res = validate_country_strict(target_country)
        if not is_v_target:
            return failure(target_c_res, 400)

        # Resolve index and economic details
        base_info = get_country_col_info(base_c_res)
        target_info = get_country_col_info(target_c_res)

        base_index = base_info["index"]
        target_index = target_info["index"]

        # 1. Currency Conversion logic
        converted_salary = None
        exchange_rate_value = None
        if base_info["exchange_rate"] is not None and target_info["exchange_rate"] is not None:
            # Convert Base to USD, then USD to Target
            usd_salary = base_salary / base_info["exchange_rate"]
            converted_salary = usd_salary * target_info["exchange_rate"]
            exchange_rate_value = target_info["exchange_rate"] / base_info["exchange_rate"]

        # 2. PPP Purchasing Power Comparison logic
        ppp_salary = None
        ppp_available = False
        if base_info["ppp_factor"] is not None and target_info["ppp_factor"] is not None:
            # PPP adjustment: Convert Base to International USD, then USD to Target
            usd_ppp = base_salary / base_info["ppp_factor"]
            ppp_salary = usd_ppp * target_info["ppp_factor"]
            ppp_available = True

        # Math Safeguards
        suspicious = False
        warning_msg = ""
        if exchange_rate_value is not None:
            if exchange_rate_value > 1000 or exchange_rate_value < 0.001:
                suspicious = True
                warning_msg = "Extreme exchange rate conversion detected."
        if ppp_available:
            ppp_ratio = target_info["ppp_factor"] / base_info["ppp_factor"]
            if ppp_ratio > 50 or ppp_ratio < 0.02:
                suspicious = True
                warning_msg = "Extreme purchasing power parity ratio detected."
            if ppp_salary <= 0:
                ppp_available = False

        # 3. Actual Market Salary Benchmark logic
        market_salary_available = False
        market_min, market_max, market_median = None, None, None
        market_min_fmt, market_max_fmt, market_median_fmt = "", "", ""
        market_reason = ""
        
        if career:
            exp_years = 4 # default Mid Level
            exp_clean = experience.lower()
            if "entry" in exp_clean or "junior" in exp_clean or "0-2" in exp_clean:
                exp_years = 1
            elif "senior" in exp_clean or "experienced" in exp_clean or "lead" in exp_clean or "6-9" in exp_clean or "10+" in exp_clean:
                exp_years = 8
                
            from salary_data_layer import get_verified_salary_data
            verified_res = get_verified_salary_data(
                career=career,
                country=target_c_res,
                city=target_city if target_city else None,
                experience_years=exp_years
            )
            
            if verified_res.get("career_valid") and verified_res.get("salary"):
                sal_data = verified_res["salary"]
                if sal_data.get("min") is not None:
                    market_salary_available = True
                    market_min = sal_data["min"]
                    market_max = sal_data["max"]
                    market_median = sal_data["median"]
                    market_min_fmt = sal_data.get("min_fmt") or f"{target_info['currency_symbol']}{market_min:,.0f} / yr"
                    market_max_fmt = sal_data.get("max_fmt") or f"{target_info['currency_symbol']}{market_max:,.0f} / yr"
                    market_median_fmt = sal_data.get("median_fmt") or f"{target_info['currency_symbol']}{market_median:,.0f} / yr"
                    market_reason = sal_data.get("reason") or f"Typical salary range for {career} in {target_c_res}."

        # 4. Cost of Living comparison text and category breakdowns
        if target_index < base_index:
            percent_diff = ((base_index - target_index) / base_index) * 100
            comparison_text = f"{target_c_res} is {percent_diff:.1f}% cheaper to live in than {base_c_res}."
        elif target_index > base_index:
            percent_diff = ((target_index - base_index) / base_index) * 100
            comparison_text = f"{target_c_res} is {percent_diff:.1f}% more expensive to live in than {base_c_res}."
        else:
            percent_diff = 0.0
            comparison_text = f"The cost of living in {target_c_res} is equivalent to {base_c_res}."

        # Dynamic, logical category index multipliers (purely for comparison, does NOT determine PPP salary)
        base_housing = base_index * 0.75
        target_housing = target_index * 1.2 if target_index > base_index else target_index * 0.75
        housing_diff = ((target_housing - base_housing) / base_housing) * 100
        
        base_food = base_index * 1.1
        target_food = target_index * 1.05
        food_diff = ((target_food - base_food) / base_food) * 100
        
        base_trans = base_index * 0.9
        target_trans = target_index * 0.95
        trans_diff = ((target_trans - base_trans) / base_trans) * 100
        
        base_util = base_index * 1.0
        target_util = target_index * 1.1
        util_diff = ((target_util - base_util) / base_util) * 100

        # 5. Intelligent relocation analysis paragraph
        base_amt_str = f"{base_info['currency_symbol']}{base_salary:,.0f}"
        conv_amt_str = f"{target_info['currency_symbol']}{converted_salary:,.0f}" if converted_salary else "N/A"
        ppp_amt_str = f"{target_info['currency_symbol']}{ppp_salary:,.0f}" if ppp_salary else "N/A"
        
        if market_salary_available:
            market_range_str = f"{target_info['currency_symbol']}{market_min:,.0f}–{target_info['currency_symbol']}{market_max:,.0f}"
        else:
            market_range_str = "unavailable"
            
        location_desc = f"{target_city}, {target_c_res}" if target_city else target_c_res
        
        analysis_paragraph = (
            f"Your current salary of {base_amt_str} has a currency equivalent of approximately {conv_amt_str}. "
            f"The PPP comparison estimates its relative purchasing power at approximately {ppp_amt_str}. "
            f"However, this is not the salary you should expect to earn in {target_c_res}. "
            f"For a {career} with {experience} experience in {location_desc}, the relevant market salary range is {market_range_str}."
        )

        # Generate custom insights via LLM
        prompt = f"""
You are an expert International Compensation Analyst.
A professional is evaluating relocation:
- Base Country: {base_c_res}
- Target Country: {target_c_res}
- Career: {career} ({experience} level)
- Base Salary: {base_amt_str}
- Currency Exchange Equivalent: {conv_amt_str}
- PPP Purchasing Power Equivalent: {ppp_amt_str}
- Local Market Salary Range: {market_range_str}

Provide exactly 3 short bullet points (under 16 words each) about the relocation impact.
Return ONLY a valid JSON list of 3 strings. Example: ["tip 1", "tip 2", "tip 3"]. Do not return markdown.
"""
        tips = []
        try:
            llm_text = generate_with_fallback(prompt)
            cleaned = clean_json(llm_text)
            tips = json.loads(cleaned)
        except Exception as e:
            print(f"LLM CoL tips generation error: {e}")
            
        # Fallback default tips if LLM fails
        if not tips or not isinstance(tips, list) or len(tips) < 3:
            if target_index < base_index:
                tips = [
                    f"Rent and monthly utility costs are significantly lower in {target_c_res}.",
                    "Your local purchasing power will increase, allowing for higher monthly savings.",
                    f"Aim to negotiate above {ppp_amt_str} to improve your savings rate."
                ]
            else:
                tips = [
                    f"Expect substantially higher rent and housing costs in {target_c_res}.",
                    "Daily expenses and services will require a higher budget allocation.",
                    f"Negotiate for at least {ppp_amt_str} to maintain your current lifestyle."
                ]

        result = {
            "success": True,
            "base_country": base_c_res,
            "target_country": target_c_res,
            "career": career,
            "experience": experience,
            "target_city": target_city,
            "base_salary": base_salary,
            "base_currency_code": base_info["currency_code"],
            "base_currency_symbol": base_info["currency_symbol"],
            "target_currency_code": target_info["currency_code"],
            "target_currency_symbol": target_info["currency_symbol"],
            
            "currency_conversion": {
                "converted_salary": converted_salary,
                "exchange_rate": exchange_rate_value,
                "explanation": "Converted directly using the market exchange rate."
            },
            
            "ppp_comparison": {
                "ppp_salary": ppp_salary,
                "ppp_available": ppp_available,
                "ppp_factor_base": base_info["ppp_factor"],
                "ppp_factor_target": target_info["ppp_factor"],
                "explanation": "Based on World Bank/OECD Purchasing Power Parity (PPP) conversion factors for 2026. This represents what target currency amount is needed to match the domestic purchasing power of your base salary."
            },
            
            "market_salary": {
                "available": market_salary_available,
                "min": market_min,
                "max": market_max,
                "median": market_median,
                "min_fmt": market_min_fmt,
                "max_fmt": market_max_fmt,
                "median_fmt": market_median_fmt,
                "reason": market_reason
            },
            
            "cost_of_living": {
                "available": True,
                "base_col_index": base_index,
                "target_col_index": target_index,
                "percent_diff": percent_diff,
                "comparison_text": comparison_text,
                "categories": {
                    "Housing": {"base": base_housing, "target": target_housing, "diff": housing_diff},
                    "Food": {"base": base_food, "target": target_food, "diff": food_diff},
                    "Transportation": {"base": base_trans, "target": target_trans, "diff": trans_diff},
                    "Utilities": {"base": base_util, "target": target_util, "diff": util_diff},
                    "General": {"base": base_index, "target": target_index, "diff": percent_diff}
                }
            },
            
            "intelligent_analysis": analysis_paragraph,
            "insights": tips,
            "suspicious": suspicious,
            "warning": warning_msg
        }
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return failure("An error occurred during Cost of Living calculation.", 500)

# =====================================================
# Run Flask
# =====================================================

import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )