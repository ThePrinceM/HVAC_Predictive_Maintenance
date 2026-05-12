"""
Grok API client for HVAC AI Insights.
Uses xAI's OpenAI-compatible endpoint.
"""
import os
import json
import requests
from typing import Iterator

def _get_secret(key, default=""):
    """Get secret from env var or Streamlit Cloud secrets."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default

GROK_BASE_URL = _get_secret("GROK_BASE_URL", "https://api.x.ai/v1")
GROK_MODEL    = _get_secret("GROK_MODEL", "grok-3")
GROK_API_KEY  = _get_secret("GROK_API_KEY", "")


SYSTEM_PROMPT = """You are an expert HVAC predictive maintenance engineer with deep knowledge 
of Rooftop Units (RTUs). You analyze real-time sensor data and AI fault predictions to provide 
actionable insights. Be concise, technical but accessible, and always suggest concrete next steps.
Format your responses with clear sections. Never make up sensor values — only use what is provided."""

def build_sensor_context(reading: dict, prediction: dict) -> str:
    """Format current sensor reading + prediction as context for Grok."""
    lines = ["## Current RTU Sensor Reading"]
    for k, v in reading.items():
        if k != "fault":
            lines.append(f"- {k.replace('_', ' ').title()}: {v}")
    lines.append(f"\n## AI Prediction")
    lines.append(f"- Predicted Fault: **{prediction.get('predicted_class', 'Unknown')}**")
    lines.append(f"- Confidence: {prediction.get('confidence', 0)*100:.1f}%")
    probs = prediction.get("probabilities", {})
    if probs:
        lines.append("- All class probabilities:")
        for cls, prob in sorted(probs.items(), key=lambda x: -x[1]):
            lines.append(f"  - {cls}: {prob*100:.1f}%")
    return "\n".join(lines)

def get_initial_insight(reading: dict, prediction: dict) -> str:
    """
    Generate the opening real-time insight paragraph (non-streaming, for speed).
    Returns full text string.
    """
    api_key = _get_secret("GROK_API_KEY", "")
    base_url = _get_secret("GROK_BASE_URL", "https://api.x.ai/v1")
    model_name = _get_secret("GROK_MODEL", "grok-3")

    if not api_key:
        return "⚠️ Grok API key not configured. Add GROK_API_KEY to your .env file."
    
    context = build_sensor_context(reading, prediction)
    user_message = f"""{context}

Based on this real-time data, provide a concise 3-paragraph analysis:
1. What the current sensor readings indicate about the RTU's health
2. Why the AI predicted this specific fault class (or Normal)
3. The top 2 recommended immediate actions for the maintenance team"""

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 400,
                "temperature": 0.3
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⚠️ Grok API timed out. Check your connection and API key."
    except Exception as e:
        return f"⚠️ Grok API error: {str(e)}"

def stream_chat_response(messages: list) -> Iterator[str]:
    """
    Stream a chat response from Grok given a full conversation history.
    Yields text chunks as they arrive (SSE streaming).
    """
    api_key = _get_secret("GROK_API_KEY", "")
    base_url = _get_secret("GROK_BASE_URL", "https://api.x.ai/v1")
    model_name = _get_secret("GROK_MODEL", "grok-3")

    if not api_key:
        yield "⚠️ Grok API key not configured."
        return

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_name,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "max_tokens": 600,
                "temperature": 0.4,
                "stream": True
            },
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                data = line[6:]
                if data == b"[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"\n⚠️ Stream error: {str(e)}"
