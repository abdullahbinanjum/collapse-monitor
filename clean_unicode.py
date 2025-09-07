import re

with open("ai_analysis.py", "r", encoding="utf-8") as f:
    content = f.read()

# Normalize curly quotes and apostrophes
content = content.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

# Remove any other non-ASCII characters
content = re.sub(r"[^\x00-\x7F]", "", content)

with open("ai_analysis.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ ai_analysis.py cleaned successfully.")
