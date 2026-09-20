from flask import Flask, request, jsonify, send_from_directory
import os
import requests

app = Flask(__name__, static_folder='.')

EPR_KB = {
    "us": "US EPR (California SB54): Register with Circular Action Alliance (CAA) as PRO, 25% source reduction by 2032, 65% recycling, $500M fund, $150/ton base fee.",
    "uk": "UK EPR (PackUK): Register on PackUK portal, biannual data, modulated fees by RAM (Red/Amber/Green), £485/ton. Small producer exempt if <£1M & <25T.",
    "eu": "EU PPWR: DRS, 65% recycling 2025, 70% 2030, PROs CITEO (FR), Grune Punkt (DE).",
    "jp": "Japan Containers & Packaging Recycling Law: JCPRA fees, 8 materials, 3R obligations.",
    "in": "India Plastic Waste Rules (CPCB): PIBO registration, targets Q1 25%, Q2 70% (current), Q3 100%."
}

def rule_based_answer(q):
    ql = q.lower()
    if any(x in ql for x in ['us','california','sb54','caa']): return EPR_KB['us']
    if any(x in ql for x in ['uk','packuk','defra','ram']): return EPR_KB['uk']
    if any(x in ql for x in ['eu','ppwr']): return EPR_KB['eu']
    if any(x in ql for x in ['japan','jp','jcpra']): return EPR_KB['jp']
    if any(x in ql for x in ['india','cpcb','pibo']): return EPR_KB['in']
    return f"Global EPR: US=CAA $150/T, UK=PackUK £485/T + RAM, EU=PPWR, JP=JCPRA, IN=CPCB 70%. Query: {q}"

def call_gemini(question):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        system = """You are Global EPR Hub AI Agent - Expert on:
        - US: California SB54, Circular Action Alliance (CAA) PRO, $150/ton, CalRecycle, 25% reduction by 2032, 65% recycling
        - UK: PackUK portal, £485/ton base fee, RAM Red/Amber/Green modulated fees, DEFRA, Small producer exempt if turnover <£1M AND packaging <25T
        - EU: PPWR, DRS, 65% 2025 / 70% 2030 recycling, PROs CITEO France, Der Grune Punkt Germany
        - Japan: JCPRA, Containers & Packaging Recycling Law, 8 materials, 3R
        - India: CPCB EPR portal, PIBO registration, Q1 25% Q2 70% Q3 100% targets, buyback certificates
        
        User may ask in Tanglish (Tamil+English). Answer in concise bullets, give exact fees/targets, mention PRO name and exemption thresholds. Max 180 words. Be accurate."""
        
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\nUser question: {question}"}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500}
        }
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Gemini error {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        print(f"Gemini exception: {e}")
        return None

def call_groq(question):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: return None
    try:
        system_prompt = "You are Global EPR Hub expert. US SB54 CAA $150/ton, UK PackUK £485/ton RAM, EU PPWR DRS, Japan JCPRA, India CPCB 70%. Answer concise bullets, exact fees, exemption UK <£1M & <25T. Tanglish allowed. Max 180 words."
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}],
                "temperature": 0.3, "max_tokens": 500
            },
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
        return None
    except: return None

@app.route('/')
def home(): return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if path == 'ask': return jsonify({"error": "Use POST"}), 405
    return send_from_directory('.', path)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    q = data.get('question','').strip()
    if not q: return jsonify({"answer": "Please ask EPR question"}), 400
    
    # GEMINI FIRST (user preference)
    answer = call_gemini(q)
    source = "gemini-1.5-flash"
    if not answer:
        answer = call_groq(q)
        source = "groq-llama-3.1"
    if not answer:
        answer = rule_based_answer(q)
        source = "rule-based-fallback (add GEMINI_API_KEY in Render Env for AI)"
    
    return jsonify({"answer": answer, "source": source})

@app.route('/health')
def health():
    return jsonify({
        "status": "live",
        "has_gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "has_groq": bool(os.environ.get("GROQ_API_KEY")),
        "version": "4-in-1 EPR Agent v2 - Gemini Priority"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
