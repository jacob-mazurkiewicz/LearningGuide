"""
ai_service.py — AI Plan Generation
====================================

This module handles communication with AI providers to automatically
generate learning plans based on a user's topic.

Supported providers:
    1. Groq   — Fast, free tier. Set GROQ_API_KEY in .env
    2. OpenAI — Most popular. Set OPENAI_API_KEY in .env
    3. Ollama — Free, local model. No key needed. Set OLLAMA_BASE_URL in .env

The module tries providers in order: Groq → OpenAI → Ollama.
If none are configured, it raises a helpful error.

How it works:
    1. Build a "prompt" describing what we want the AI to produce.
    2. Send the prompt to the AI API.
    3. Parse the AI's JSON response into our plan structure.
    4. Return the structured plan to the caller.
"""

import os
import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# The system prompt tells the AI what role to play and how to format output.
SYSTEM_PROMPT = """You are an expert learning coach and curriculum designer.
Your job is to create detailed, actionable learning plans.
Always respond with valid JSON only — no markdown, no prose, just pure JSON.
"""

# The template for the user's request to the AI.
USER_PROMPT_TEMPLATE = """Create a learning plan for: "{topic}"

Plan duration: {duration_weeks} weeks
Daily time commitment: {hours_per_day} hours/day

Return a JSON object with this exact structure:
{{
  "plan_title": "Concise plan title",
  "plan_description": "1-2 sentence overview of the plan",
  "goals": [
    {{
      "title": "Goal title",
      "description": "What this goal covers",
      "subtasks": [
        {{
          "title": "Subtask title",
          "description": "What this subtask involves",
          "daily_tasks": [
            {{
              "title": "Specific daily task",
              "description": "What to do",
              "estimated_minutes": 30
            }}
          ]
        }}
      ]
    }}
  ]
}}

Guidelines:
- Create 2-4 major goals that span the {duration_weeks} weeks
- Each goal should have 2-4 subtasks
- Each subtask should have 3-5 daily tasks
- Daily tasks should be concrete and actionable
- Keep estimated_minutes realistic given {hours_per_day} hours/day
- Titles should be short (under 60 chars); descriptions can be longer
"""


def _clean_json_response(text: str) -> str:
    """
    Extract JSON from the AI response, handling cases where the AI
    wraps the JSON in markdown code blocks like ```json ... ```.
    """
    # Remove markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.strip()
    # Find the first { and last } to extract the JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in AI response")
    return text[start:end]


def _try_groq(prompt_messages: list, model: str = "llama-3.1-8b-instant") -> Optional[str]:
    """
    Try to generate content using Groq's API.

    Groq is very fast and has a generous free tier.
    Get your key at: https://console.groq.com
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except ImportError:
        logger.warning("groq package not installed. Run: pip install groq")
        return None
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None


def _try_openai(prompt_messages: list, model: str = "gpt-4o-mini") -> Optional[str]:
    """
    Try to generate content using OpenAI's API (or any OpenAI-compatible API).

    Get your key at: https://platform.openai.com
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
        base_url = os.getenv("OPENAI_BASE_URL")  # Optional: override for other providers
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    except ImportError:
        logger.warning("openai package not installed. Run: pip install openai")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _try_ollama(prompt_messages: list, model: str = "llama3.2") -> Optional[str]:
    """
    Try to generate content using a local Ollama server.

    Ollama is completely free and runs models locally on your machine.
    Install from: https://ollama.com
    Then run: ollama pull llama3.2
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", model)

    try:
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "model": ollama_model,
            "messages": prompt_messages,
            "stream": False,
            "options": {"temperature": 0.7},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None


def generate_learning_plan(topic: str, duration_weeks: int = 4, hours_per_day: float = 1.0) -> dict:
    """
    Generate a learning plan for the given topic using an AI model.

    Tries providers in order: Groq → OpenAI → Ollama.
    Returns a dict matching the AIGenerateResponse schema.

    Args:
        topic: What the user wants to learn or build.
        duration_weeks: How many weeks the plan should span.
        hours_per_day: How many hours per day the user can commit.

    Returns:
        A dict with keys: plan_title, plan_description, goals.

    Raises:
        RuntimeError: If no AI provider is configured or all fail.
        ValueError: If the AI returns invalid JSON.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                topic=topic,
                duration_weeks=duration_weeks,
                hours_per_day=hours_per_day,
            ),
        },
    ]

    # Try each provider in order
    raw_response = (
        _try_groq(messages)
        or _try_openai(messages)
        or _try_ollama(messages)
    )

    if raw_response is None:
        raise RuntimeError(
            "No AI provider is configured. Please set GROQ_API_KEY, "
            "OPENAI_API_KEY, or ensure Ollama is running locally. "
            "See .env.example for instructions."
        )

    # Parse and validate the JSON response
    try:
        clean = _clean_json_response(raw_response)
        data = json.loads(clean)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"AI returned invalid JSON: {e}\nRaw response: {raw_response[:500]}")

    # Validate required fields
    required = ["plan_title", "plan_description", "goals"]
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"AI response missing required fields: {missing}")

    return data
