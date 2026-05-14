from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Ollama runs as a separate container on the same Docker network
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "tinyllama")


@app.route("/health", methods=["GET"])
def health():
    """Health check — pipeline uses this to verify deploy success."""
    return jsonify({"status": "OK", "app": "Qualibytes GPT Backend", "model": MODEL_NAME})


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Accepts conversation history and returns AI reply.
    Request body: { "messages": [{ "role": "user", "content": "..." }, ...] }
    """
    data = request.get_json()

    if not data or "messages" not in data:
        return jsonify({"error": "messages field is required"}), 400

    messages = data["messages"]
    if not isinstance(messages, list) or len(messages) == 0:
        return jsonify({"error": "messages must be a non-empty list"}), 400

    # Add a system prompt so tinyllama behaves as Qualibytes GPT
    system_message = {
        "role": "system",
        "content": (
            "You are Qualibytes GPT, a helpful and friendly AI assistant. "
            "You give clear, concise answers. Keep responses short and to the point."
        )
    }

    full_messages = [system_message] + messages

    try:
        # Call Ollama /api/chat endpoint (supports multi-turn conversation)
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": full_messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 300    # Limit response length for t2.small
                }
            },
            timeout=90   # tinyllama can be slow on small instances
        )
        response.raise_for_status()

        result = response.json()
        reply = result["message"]["content"].strip()
        return jsonify({"reply": reply})

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Ollama service is not reachable. Is it running?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Ollama timed out. Model may still be loading — try again."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
