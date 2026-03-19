import asyncio
import base64
import json
import logging
import os
import shutil
import tempfile

import claude_code_sdk._internal.message_parser as _mp
import claude_code_sdk._internal.client as _client
from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    UserMessage,
    McpStdioServerConfig,
)

from prompts import get_system_prompt

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 270  # seconds — competition allows 300s, leave buffer
MCP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tripletex_mcp.py")

# Monkey-patch the SDK message parser to skip unknown message types
# instead of crashing. The SDK doesn't handle rate_limit_event etc.
_original_parse = _mp.parse_message


def _patched_parse(data):
    try:
        return _original_parse(data)
    except _mp.MessageParseError as e:
        if "Unknown message type" in str(e):
            logger.debug(f"Skipping unknown message type: {data.get('type')}")
            return SystemMessage(subtype=data.get("type", "unknown"), data=data)
        raise


_mp.parse_message = _patched_parse
_client.parse_message = _patched_parse


def build_agent_prompt(prompt: str, files: list) -> str:
    """Build the prompt for Claude Code including the task and file info."""
    parts = [
        f"Execute this Tripletex accounting task:\n\n{prompt}\n",
        "You have the `mcp__tripletex__api_call` tool available. Use it to make API calls.",
        "Do NOT use Bash, Read, Write, or any other tool. Only use `mcp__tripletex__api_call`.",
        "",
    ]

    if files:
        parts.append(f"{len(files)} file(s) attached and saved to working directory:")
        for f in files:
            parts.append(f"  - {f.get('filename', 'attachment')} ({f['mime_type']})")
        parts.append("")

    parts.append("When done, say DONE.")

    return "\n".join(parts)


async def run_agent(prompt: str, files: list, credentials: dict) -> None:
    """Run the Claude Code SDK agent to complete an accounting task."""
    logger.info(f"Starting Claude Code agent for task: {prompt[:150]}...")

    work_dir = tempfile.mkdtemp(prefix="tripletex_")

    try:
        for f in files:
            filename = f.get("filename", "attachment")
            filepath = os.path.join(work_dir, filename)
            data = base64.b64decode(f["content_base64"])
            with open(filepath, "wb") as fh:
                fh.write(data)
            logger.info(f"Saved attachment: {filepath} ({len(data)} bytes)")

        agent_prompt = build_agent_prompt(prompt, files)

        options = ClaudeCodeOptions(
            append_system_prompt=get_system_prompt(),
            allowed_tools=["mcp__tripletex__api_call", "ToolSearch"],
            mcp_servers={
                "tripletex": McpStdioServerConfig(
                    command="python",
                    args=[MCP_SCRIPT],
                    env={
                        "TX_BASE_URL": credentials["base_url"],
                        "TX_TOKEN": credentials["session_token"],
                    },
                ),
            },
            max_turns=30,
            cwd=work_dir,
            permission_mode="bypassPermissions",
        )

        async with asyncio.timeout(AGENT_TIMEOUT):
            async for message in query(prompt=agent_prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, "text"):
                            logger.info(f"Agent: {block.text[:300]}")
                        elif hasattr(block, "name") and hasattr(block, "input"):
                            input_str = json.dumps(block.input, ensure_ascii=False)[:500]
                            logger.info(f"Agent tool: {block.name} → {input_str}")
                        elif hasattr(block, "tool_use_id"):
                            content = str(block.content)[:800] if block.content else ""
                            logger.info(f"Tool result: {content}")
                elif isinstance(message, UserMessage):
                    if hasattr(message, "content") and isinstance(message.content, list):
                        for block in message.content:
                            if hasattr(block, "tool_use_id"):
                                content = str(block.content)[:800] if block.content else ""
                                logger.info(f"Tool result: {content}")
                elif isinstance(message, ResultMessage):
                    logger.info(
                        f"Agent finished: turns={message.num_turns}, "
                        f"duration={message.duration_ms}ms, "
                        f"error={message.is_error}"
                    )
                    if message.is_error:
                        logger.error(f"Agent error result: {message.result}")

    except TimeoutError:
        logger.warning(f"Agent timed out after {AGENT_TIMEOUT}s")
    except Exception as e:
        logger.error(f"Claude Code SDK error: {e}")
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    logger.info("Agent completed")
