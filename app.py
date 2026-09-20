from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='.')

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    q = data.get('question','').lower()
    # Simple rule-based global EPR agent logic (expand later)
    if 'us' in q and 'uk' in q:
        ans = "US (SB54): CAA as PRO, 25% reduction by 2032, $500M fund. UK: PackUK, modulated fees based on RAM (Red/Amber/Green), 2025 data report due."
    elif 'us' in q:
        ans = "US EPR (California SB54): Register with Circular Action Alliance (CAA), report packaging weight, pay fees, meet 25% source reduction & 65% recycling by 2032."
    elif 'uk' in q:
        ans = "UK EPR: Register on PackUK portal, submit packaging data biannually, pay modulated fees per RAM rating, use PRNs."
    elif 'japan' in q or 'jp' in q:
        ans = "Japan: Containers & Packaging Recycling Law. Pay JCPRA fees, 8 materials, municipalities collect, businesses bear recycling cost."
    elif 'india' in q or 'in' in q:
        ans = "India: CPCB EPR portal, PIBO registration, plastic packaging targets Q1 25%, Q2 70%, Q3 100%. Buyback & PWM certificates."
    else:
        ans = f"Global EPR Agent: For '{q}' - Compare: US=CAA, UK=PackUK+RAM, EU=PPWR+DRS, JP=JCPRA, IN=CPCB. All require PRO registration & annual reporting."
    return jsonify({"answer": ans})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
