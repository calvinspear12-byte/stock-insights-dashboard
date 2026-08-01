# TEMPLATE (not wired on by default): let the OpenAI API rewrite the analysis blocks
# (CANDS / UPCOMING / ENTRY) in index.html automatically, so ChatGPT refreshes the
# commentary with no copy-paste. Costs a few cents per run. Complete the TODOs, add the
# OPENAI_API_KEY secret, and enable ai-refresh.yml to turn it on.
import os, re, json, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # cheap; pick any current model
KEY = os.environ["OPENAI_API_KEY"]

PROMPT = open(os.path.join(HERE, "chatgpt-refresh-prompt.txt"), encoding="utf-8").read()

def ask_openai(prompt):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"]

def replace_block(html, decl, text):
    # Replace `const NAME = ...;` up to its matching closing. TODO: for production, prefer a
    # tolerant brace/bracket matcher; this assumes the model returns a clean `const NAME = ...;`.
    m = re.search(r"const\s+" + decl + r"\s*=.*?;\n", text, re.S)
    if not m:
        print("model did not return", decl); return html
    block = m.group(0)
    pat = re.compile(r"const\s+" + decl + r"\s*=.*?\];\n" if decl != "ENTRY" else r"const\s+ENTRY\s*=.*?\};\n", re.S)
    return pat.sub(block, html, count=1)

def main():
    out = ask_openai(PROMPT)
    html = open(INDEX, encoding="utf-8").read()
    for decl in ("CANDS", "UPCOMING", "ENTRY"):
        html = replace_block(html, decl, out)
    open(INDEX, "w", encoding="utf-8").write(html)
    print("ai_refresh done")

if __name__ == "__main__":
    main()
