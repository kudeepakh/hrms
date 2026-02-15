"""
Agent orchestrator — the main AI loop.

Flow:
  1. Check FAQ registry for instant (zero-GPT-cost) answers.
  2. Check query cache for previously answered identical queries.
  3. Call OpenAI Chat Completions with function-calling tool loop.
  4. Cache the final answer.
  5. Invalidate cache on any write operation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.agent.prompt_templates import build_system_prompt
from app.agent.tools import TOOL_DEFINITIONS
from app.agent.tool_executor import execute_tool, is_write_tool
from app.cache.faq_registry import match_faq
from app.cache.query_cache import get_cached, set_cache, invalidate_cache
from app.config import get_settings
from app.models.user import User

logger = logging.getLogger("hrms.orchestrator")

# In-memory per-session conversation history
_sessions: dict[str, list[dict[str, Any]]] = {}

MAX_HISTORY = 20  # keep last N messages per session to control token usage
MAX_TOOL_ROUNDS = 8  # safety-limit on tool-calling loops


async def run_agent(
    user_message: str,
    session_id: str,
    user: User,
) -> str:
    """
    Process a user chat message and return the assistant's reply.

    Parameters
    ----------
    user_message : str
        The raw text from the user.
    session_id : str
        Unique session identifier (used for conversation memory).
    user : User
        Authenticated user document (contains role, email, emp_code).

    Returns
    -------
    str
        The assistant's final textual reply.
    """

    settings = get_settings()

    # ------------------------------------------------------------------
    # 1. FAQ check — instant answer, no API cost
    # ------------------------------------------------------------------
    faq_answer = match_faq(user_message)
    if faq_answer:
        logger.info("FAQ hit for session=%s", session_id)
        return faq_answer

    # ------------------------------------------------------------------
    # 2. Cache check — return cached response if query matches
    # ------------------------------------------------------------------
    cached = await get_cached(user_message)
    if cached:
        logger.info("Cache hit for session=%s", session_id)
        return cached.reply

    # ------------------------------------------------------------------
    # 3. Build / retrieve conversation history
    # ------------------------------------------------------------------
    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]

    # Inject system prompt (always first message)
    system_msg = {"role": "system", "content": build_system_prompt(user)}

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Trim to keep history manageable
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    # ------------------------------------------------------------------
    # 4. OpenAI tool-calling loop
    # ------------------------------------------------------------------
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    messages = [system_msg] + history
    wrote_data = False

    for _round in range(MAX_TOOL_ROUNDS):
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.3,
        )

        choice = response.choices[0]
        assistant_msg = choice.message

        # If the model wants to call tool(s)
        if assistant_msg.tool_calls:
            # Append the assistant message (with tool_calls) to messages
            messages.append(assistant_msg.model_dump())

            for tool_call in assistant_msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                logger.info(
                    "Tool call: %s(%s) session=%s",
                    fn_name,
                    json.dumps(fn_args, default=str),
                    session_id,
                )

                result = await execute_tool(fn_name, fn_args, user)

                if is_write_tool(fn_name):
                    wrote_data = True

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

            # Continue loop so the model can process tool results
            continue

        # No tool calls — we have the final reply
        final_reply = assistant_msg.content or ""
        break
    else:
        # Safety: if we exhaust MAX_TOOL_ROUNDS
        final_reply = (
            "I'm sorry, I wasn't able to complete your request. "
            "Please try rephrasing or simplifying your question."
        )

    # ------------------------------------------------------------------
    # 5. Post-processing: update history, cache, invalidation
    # ------------------------------------------------------------------
    history.append({"role": "assistant", "content": final_reply})

    if wrote_data:
        await invalidate_cache()
        logger.info("Cache invalidated due to write operation, session=%s", session_id)
    else:
        await set_cache(user_message, final_reply)

    return final_reply
