import google.generativeai as genai
from flask import Flask, request, jsonify
import requests
import os

wa_token = os.environ.get("WA_TOKEN")
genai.configure(api_key=os.environ.get("GEN_API"))
model_name = "gemini-1.5-pro"

app = Flask(__name__)

model = genai.GenerativeModel(model_name=model_name)
convo = model.start_chat(history=[])

with open("instructions.txt", "r") as f:
    commands = f.read()
convo.send_message(commands)

def send(answer, sender, phone_id):
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        'Authorization': f'Bearer {wa_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "messaging_product": "whatsapp", 
        "to": f"{sender}", 
        "type": "text",
        "text": {"body": f"{answer}"},
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response

@app.route("/", methods=["GET", "POST"])
def index():
    return "Bot"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == "BOT":
            return challenge, 200
        else:
            return "Failed", 403
    elif request.method == "POST":
        try:
            data = request.get_json()["entry"][0]["changes"][0]["value"]["messages"][0]
            phone_id = request.get_json()["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
            sender = "+" + data["from"]
            if data["type"] == "text":
                prompt = data["text"]["body"]
                convo.send_message(prompt)
                send(convo.last.text, sender, phone_id)
            else:
                send("Lo siento, solo puedo procesar mensajes de texto por ahora.", sender, phone_id)
        except Exception as e:
            print(f"Error: {str(e)}")
        return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=8000)
