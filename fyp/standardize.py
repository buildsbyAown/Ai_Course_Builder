import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Directory containing txt files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_DIR = os.path.join(BASE_DIR, "outlines_txt")

def clean_course_text(raw_text: str) -> str:
    """
    Uses Groq LLM to clean noisy course text and extract:
    - CLOs
    - Weekly content / outline
    - Recommended books
    """

    prompt = f"""
You are given raw text extracted from a university course PDF.
The text may contain:
- page numbers
- headers / footers
- broken formatting
- repeated titles
- irrelevant administrative content

🎯 Your task:
Clean and extract ONLY the following information **if it exists in the text**:
1. Course Learning Outcomes (CLOs)
2. Weekly course content / outline / schedule
3. Recommended books or references

❗ Rules:
- DO NOT invent or hallucinate content
- DO NOT summarize beyond what exists
- If a section is missing, clearly write: "Not provided in source"
- Remove all noise and unrelated content
- Keep the wording faithful to the source
- Output must be clean, readable, and structured

📌 Output Format (Markdown — follow exactly):

# Course Learning Outcomes (CLOs)
- ...

# Weekly Course Outline
## Week 1
- ...
## Week 2
- ...

# Recommended Books
- ...

Here is the raw text:
--------------------
{raw_text}
--------------------
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # low temperature to avoid hallucination
    )

    return response.choices[0].message.content.strip()


def process_txt_files():
    for file_name in os.listdir(TXT_DIR):
        if not file_name.lower().endswith(".txt"):
            continue

        file_path = os.path.join(TXT_DIR, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()

        if not raw_text:
            print(f"⚠️ Skipped empty file: {file_name}")
            continue

        print(f"🧠 Cleaning: {file_name}")

        try:
            cleaned_text = clean_course_text(raw_text)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)

            print(f"✅ Cleaned & updated: {file_name}")

        except Exception as e:
            print(f"❌ Failed on {file_name}: {e}")


if __name__ == "__main__":
    process_txt_files()
    print("🎉 All course files processed successfully.")
