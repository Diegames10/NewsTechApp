# chat_api.py
import os
from flask import Blueprint, request, jsonify
from markupsafe import escape
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

bp_chat = Blueprint("bp_chat", __name__, url_prefix="/api/chat")

MODEL_NAME = "llama-3.3-70b-versatile"

def _get_client() -> OpenAI:
    """
    Cria cliente compatível OpenAI, apontando para Groq.
    Necessário definir GROQ_API_KEY no .env
    """
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "❌ GROQ_API_KEY ausente. Crie em https://console.groq.com/keys "
            "e defina no arquivo .env"
        )
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

@bp_chat.route("/ping", methods=["GET"])
def ping():
    """Verifica se o chat está ativo"""
    return jsonify({"ok": True, "model": MODEL_NAME})

@bp_chat.route("", methods=["POST"])
def api_chat():
    """Endpoint de chat /api/chat"""
    try:
        data = request.get_json(silent=True) or {}
        user_text = (data.get("message") or "").strip()

        if not user_text:
            return jsonify({"error": "Mensagem vazia."}), 400
        if len(user_text) > 1000:
            return jsonify({"error": "Mensagem muito longa (máx. 1000 caracteres)."}), 400

        client = _get_client()

        # chamada ao modelo Groq
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Você é um assistente útil e responde em português claro."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=400,
        )

        text = (resp.choices[0].message.content or "").strip()
        return jsonify({"reply": text})

    except Exception as e:
        msg = str(e)
        if "invalid_api_key" in msg or "401" in msg:
            msg = "Chave da Groq inválida. Confira o valor da variável GROQ_API_KEY."
        elif "insufficient_quota" in msg:
            msg = "Cota gratuita esgotada. Gere uma nova chave no painel da Groq."
        return jsonify({"error": f"Falha ao gerar resposta: {escape(msg)}"}), 500
