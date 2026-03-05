#!/usr/bin/env bash
# Hook: Block access to .env files via Read, Edit, Write, Grep, etc.
# Reads the tool input JSON from stdin and checks if the target path is a .env file.

input=$(cat)
tool_name="${CLAUDE_TOOL_NAME:-}"

# Extract file_path, pattern, or command from the raw JSON input
# Avoid python3 json.load — it rejects Windows backslash paths as invalid escapes
file_path=$(echo "$input" | sed -n 's/.*"\(file_path\|pattern\|command\)"\s*:\s*"\([^"]*\)".*/\2/p' | head -1)

# Check if the path references a .env file
if echo "$file_path" | grep -qiE '(^|[/\\])\.env($|[/\\.])|\.env\b'; then
  echo "BLOCKED: Access to .env files is not allowed. These files contain secrets."
  exit 2
fi

exit 0
