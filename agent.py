import base64
import logging
import os
import tempfile

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import AssistantMessage, ResultMessage

from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def build_agent_prompt(prompt: str, files: list, credentials: dict) -> str:
    """Build the full prompt for Claude Code including task, credentials, and file info."""
    base_url = credentials["base_url"]
    token = credentials["session_token"]

    parts = [
        f"Execute this Tripletex accounting task:\n\n{prompt}\n",
        f"Tripletex API credentials:",
        f"  Base URL: {base_url}",
        f'  Authentication: Basic auth with username "0" and password "{token}"',
        "",
        "Use Python with httpx (already installed) to make API calls. Example:",
        f'  import httpx',
        f'  resp = httpx.get("{base_url}/employee", auth=("0", "{token}"), params={{"fields": "id,firstName,lastName"}})',
        f'  print(resp.status_code, resp.json())',
        "",
    ]

    # Handle file attachments
    if files:
        parts.append(f"\n{len(files)} file(s) attached. They have been saved to the working directory:")
        for f in files:
            parts.append(f"  - {f.get('filename', 'attachment')} ({f['mime_type']})")
        parts.append("")

    parts.append("When done, just say DONE. Do not return any code — execute everything directly.")

    return "\n".join(parts)


async def run_agent(prompt: str, files: list, credentials: dict) -> None:
    """Run the Claude Code SDK agent to complete an accounting task."""
    logger.info(f"Starting Claude Code agent for task: {prompt[:150]}...")

    # Save any attached files to a temp directory
    work_dir = tempfile.mkdtemp(prefix="tripletex_")

    for f in files:
        filename = f.get("filename", "attachment")
        filepath = os.path.join(work_dir, filename)
        data = base64.b64decode(f["content_base64"])
        with open(filepath, "wb") as fh:
            fh.write(data)
        logger.info(f"Saved attachment: {filepath} ({len(data)} bytes)")

    agent_prompt = build_agent_prompt(prompt, files, credentials)

    options = ClaudeCodeOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Bash", "Read", "Write"],
        max_turns=25,
        cwd=work_dir,
        permission_mode="bypassPermissions",
    )

    try:
        async for message in query(prompt=agent_prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        logger.info(f"Agent: {block.text[:300]}")
                    elif hasattr(block, "name"):
                        logger.info(f"Agent tool: {block.name}")
            elif isinstance(message, ResultMessage):
                logger.info(
                    f"Agent finished: turns={message.num_turns}, "
                    f"duration={message.duration_ms}ms, "
                    f"error={message.is_error}"
                )
                if message.is_error:
                    logger.error(f"Agent error result: {message.result}")
    except Exception as e:
        logger.error(f"Claude Code SDK error: {e}")
        raise

    logger.info("Agent completed")
