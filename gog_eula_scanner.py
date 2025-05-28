import os
import glob
import re
import time
import csv
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import PyPDF2
import openai
import docx
from striprtf.striprtf import rtf_to_text
import sys

# ---- Dependency check and helpful error message ----
required_modules = [
    "requests",
    "beautifulsoup4",
    "tqdm",
    "openai",
    "PyPDF2",
    "python_docx",
    "striprtf",
]

missing = []
for mod in required_modules:
    try:
        if mod == "beautifulsoup4":
            __import__("bs4")
        elif mod == "python_docx":
            __import__("docx")
        else:
            __import__(mod)
    except ImportError:
        missing.append(mod if mod != "python_docx" else "python-docx")

if missing:
    print("\nERROR: Missing dependencies detected!")
    print("To install them, run:")
    print(f"python -m pip install {' '.join(missing)}")
    sys.exit(1)

# ---------------- CONFIGURATION ----------------
OPENAI_API_KEY = ""  # Optionally paste your key here, or leave blank to use env variable
GOG_PATH = r"C:\Program Files (x86)\GOG Galaxy\Games"  # Change if your GOG is elsewhere
API_DELAY = 2  # seconds between API calls
OUTPUT_FILE = "gog_eula_privacy_report.csv"
EULA_DUMP_FILE = "gog_eula_dump.txt"  # File to save raw EULA texts

# ---------------- OPENAI CLIENT SETUP ----------------
api_key = os.environ.get("OPENAI_API_KEY", OPENAI_API_KEY)
openai_enabled = True
if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
    print("\nWARNING: OpenAI API key not set.")
    print(
        "OpenAI analysis will be skipped. Set the OPENAI_API_KEY environment variable or paste your key into the script to enable AI privacy checking.\n"
    )
    openai_enabled = False
else:
    client = openai.OpenAI(api_key=api_key)


# ---------------- WHITESPACE CLEANER ----------------
def clean_eula_text(text):
    text = text.replace('\t', ' ')
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(line.strip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------- HELPER FUNCTIONS ----------------
def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def is_close_match(game_name, filename):
    norm_game = normalize(game_name)
    norm_file = normalize(filename)
    return norm_game in norm_file or norm_file in norm_game


def content_matches_game(game_name, content):
    norm_game = normalize(game_name)
    norm_content = normalize(content)
    return norm_game in norm_content


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text


def extract_text_from_docx(docx_path):
    text = ""
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
    return text


def extract_text_from_rtf(rtf_path):
    text = ""
    try:
        with open(rtf_path, "r", encoding="utf-8", errors="ignore") as f:
            rtf_content = f.read()
            text = rtf_to_text(rtf_content)
    except Exception as e:
        print(f"Error reading RTF {rtf_path}: {e}")
    return text


def extract_text_from_html(html_path):
    text = ""
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            text = soup.get_text(separator="\n")
    except Exception as e:
        print(f"Error reading HTML {html_path}: {e}")
    return text


def extract_text_by_extension(file):
    ext = os.path.splitext(file)[1].lower()
    if ext == ".txt":
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT {file}: {e}")
    elif ext == ".pdf":
        return extract_text_from_pdf(file)
    elif ext == ".rtf":
        return extract_text_from_rtf(file)
    elif ext == ".docx":
        return extract_text_from_docx(file)
    elif ext in [".html", ".htm"]:
        return extract_text_from_html(file)
    return ""


def get_eula_text_from_game_files(game_name, game_path):
    eula_texts = []
    patterns = [
        "**/*eula*.txt",
        "**/*license*.txt",
        "**/*legal*.txt",
        "**/*eula*.pdf",
        "**/*license*.pdf",
        "**/*legal*.pdf",
        "**/*eula*.rtf",
        "**/*license*.rtf",
        "**/*legal*.rtf",
        "**/*eula*.docx",
        "**/*license*.docx",
        "**/*legal*.docx",
        "**/*eula*.html",
        "**/*license*.html",
        "**/*legal*.html",
        "**/*eula*.htm",
        "**/*license*.htm",
        "**/*legal*.htm",
        "**/*readme*.txt",
        "**/*manual*.txt",
    ]

    candidate_files = set()
    for pattern in patterns:
        for file in glob.glob(os.path.join(game_path, pattern), recursive=True):
            candidate_files.add(file)

    for file in candidate_files:
        filename = os.path.basename(file)
        file_text = extract_text_by_extension(file)
        if is_close_match(game_name, filename):
            eula_texts.append((file, file_text, "filename-match"))
        elif content_matches_game(game_name, file_text):
            eula_texts.append((file, file_text, "content-match"))

    if not eula_texts:
        root_patterns = [
            "eula*.txt",
            "license*.txt",
            "legal*.txt",
            "eula*.pdf",
            "license*.pdf",
            "legal*.pdf",
            "eula*.rtf",
            "license*.rtf",
            "legal*.rtf",
            "eula*.docx",
            "license*.docx",
            "legal*.docx",
            "eula*.html",
            "license*.html",
            "legal*.html",
            "readme*.txt",
            "manual*.txt",
        ]

        for pattern in root_patterns:
            for file in glob.glob(os.path.join(game_path, pattern)):
                file_text = extract_text_by_extension(file)
                if file_text.strip():
                    eula_texts.append((file, file_text, "generic-root"))

    return eula_texts


def analyze_eula_with_ai(eula_text):
    if not eula_text:
        return "No EULA found", ""

    prompt = (
        "You are a privacy expert. Analyze the following End User License Agreement (EULA) "
        "for privacy-related red flags, such as data collection, third-party sharing, user tracking, or invasive permissions. "
        "Respond with either 'Privacy risk' or 'No issues', then a short explanation. "
        "EULA:\n\n" + eula_text[:4000]
    )

    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=300,
            temperature=0.0,
        )

        return response.choices[0].text.strip(), ""
    except Exception as e:
        if hasattr(e, "message") and ("insufficient_quota" in str(e) or "quota" in str(e)):
            return "Quota exceeded", str(e)
        if "insufficient_quota" in str(e) or "quota" in str(e):
            return "Quota exceeded", str(e)
        return "AI analysis failed", str(e)


def get_installed_gog_games(gog_path):
    games = []
    for game_dir in os.listdir(gog_path):
        game_path = os.path.join(gog_path, game_dir)
        if os.path.isdir(game_path):
            game_name = game_dir  # Using the directory name as the game name
            games.append({"name": game_name, "path": game_path})
    return games


# ---------------- MAIN PROCESS ----------------
def main():
    print("Scanning GOG Galaxy games...")
    games = get_installed_gog_games(GOG_PATH)
    print(f"Found {len(games)} installed GOG games.")

    results = []
    quota_exceeded = False  # Track quota error

    # Clear the EULA dump file at the start
    with open(EULA_DUMP_FILE, "w", encoding="utf-8") as f:
        f.write("")

    for game in tqdm(games, desc="Processing games"):
        name = game["name"]
        path = game["path"]
        eula_text = None
        eula_sources = []

        # Try local files with filename/content matching
        local_eulas = get_eula_text_from_game_files(name, path)
        for file_path, text, match_type in local_eulas:
            eula_sources.append((file_path, text, match_type))

        # Choose the "best" EULA for AI analysis (prefer API/Store, else filename/content match, else generic-root)
        eula_for_ai = None
        for src, txt, match_type in eula_sources:
            if match_type in ("filename-match", "content-match"):
                eula_for_ai = txt
                break
        if not eula_for_ai and eula_sources:
            eula_for_ai = eula_sources[0][1]

        # Dump all found EULAs for this game, cleaned up
        with open(EULA_DUMP_FILE, "a", encoding="utf-8") as f:
            f.write(f"-------------------- {name} --------------------\n")
            if eula_sources:
                for src, txt, match_type in eula_sources:
                    f.write(f"[Source: {src} | Match: {match_type}]\n")
                    cleaned_txt = clean_eula_text(txt)
                    f.write(cleaned_txt)
                    f.write("\n\n")
            else:
                f.write("[No EULA found]\n\n")

        status, error = "No EULA found", ""
        if eula_for_ai and not quota_exceeded and openai_enabled:
            status, error = analyze_eula_with_ai(eula_for_ai)

        if "Quota exceeded" in status or "insufficient_quota" in error:
            print(
                "OpenAI quota exceeded. Stopping further AI analysis, but will continue dumping EULAs."
            )
            quota_exceeded = True  # Don't break, just skip AI analysis
        elif not openai_enabled:
            status, error = "Skipped (no API key)", ""

        results.append([name, path, "Yes" if eula_sources else "No", status, error])
        time.sleep(API_DELAY)

    # Write results to CSV
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Game Name", "Install Path", "EULA Found", "Privacy Assessment", "Error/Notes"]
        )
        writer.writerows(results)

    print(f"\nDone! Results saved to {OUTPUT_FILE}")
    print(f"All EULAs dumped to {EULA_DUMP_FILE}")


if __name__ == "__main__":
    main()
