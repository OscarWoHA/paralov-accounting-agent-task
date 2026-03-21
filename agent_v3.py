import asyncio
import base64
import json
import logging
import os
import shutil
import tempfile

import claude_code_sdk._internal.message_parser as _mp
import claude_code_sdk._internal.client as _client
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from claude_code_sdk.types import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    UserMessage,
    McpStdioServerConfig,
)

from prompts_v3 import get_system_prompt

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 290  # seconds — competition allows 300s
MCP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tripletex_mcp_v3.py")

# Monkey-patch the SDK message parser to skip unknown message types
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
    """Build the prompt — lean, trust the model."""
    parts = [
        f"TASK:\n{prompt}\n",
    ]

    if files:
        parts.append(f"ATTACHMENTS ({len(files)}):")
        for f in files:
            parts.append(f"  - {f.get('filename', 'attachment')} ({f['mime_type']})")
        parts.append("Read attachments with the Read tool to extract data.\n")

    parts.append("Execute now. Say DONE when finished.")

    return "\n".join(parts)


async def run_agent(prompt: str, files: list, credentials: dict) -> None:
    """Run an isolated Claude Code SDK client per request."""
    logger.info(f"Starting agent for task: {prompt[:150]}...")

    work_dir = tempfile.mkdtemp(prefix="tripletex_")

    # Also save attachments to sessions dir for debugging
    sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")

    try:
        for f in files:
            filename = f.get("filename", "attachment")
            filepath = os.path.join(work_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            data = base64.b64decode(f["content_base64"])
            with open(filepath, "wb") as fh:
                fh.write(data)
            logger.info(f"Saved attachment: {filepath} ({len(data)} bytes)")
            # Persist a copy for debugging
            ts = os.path.basename(work_dir)
            safe_name = os.path.basename(filename)
            debug_path = os.path.join(sessions_dir, f"{ts}_{safe_name}")
            with open(debug_path, "wb") as fh:
                fh.write(data)

        agent_prompt = build_agent_prompt(prompt, files)

        options = ClaudeCodeOptions(
            append_system_prompt=get_system_prompt(),
            model="sonnet",
            continue_conversation=False,
            allowed_tools=[
                "mcp__tripletex__tripletex",
                "mcp__tripletex__setup",
                "Read",
            ],
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
            disallowed_tools=[
                "AskUserQuestion",
                "Bash",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "NotebookEdit",
                "WebFetch",
                "WebSearch",
            ],
            max_turns=None,
            cwd=work_dir,
            permission_mode="bypassPermissions",
        )

        # Each request gets its own ClaudeSDKClient — fully isolated subprocess
        async with asyncio.timeout(AGENT_TIMEOUT):
            client = ClaudeSDKClient(options)
            async with client:
                await client.query(prompt=agent_prompt)
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if hasattr(block, "text"):
                                logger.info(f"Agent: {block.text}")
                            elif hasattr(block, "name") and hasattr(block, "input"):
                                input_str = json.dumps(block.input, ensure_ascii=False)
                                logger.info(f"Agent tool: {block.name} → {input_str}")
                            elif hasattr(block, "tool_use_id"):
                                content = str(block.content) if block.content else ""
                                logger.info(f"Tool result: {content}")
                    elif isinstance(message, UserMessage):
                        if hasattr(message, "content") and isinstance(message.content, list):
                            for block in message.content:
                                if hasattr(block, "tool_use_id"):
                                    content = str(block.content) if block.content else ""
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
