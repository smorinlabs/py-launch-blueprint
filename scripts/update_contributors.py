#!/usr/bin/env python3
# Copyright (c) 2025, Steve Morin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# ruff: noqa: S603
import re
import subprocess

# Identities excluded from CONTRIBUTORS.md.
# Bots usually follow the GitHub `[bot]` naming convention; one-off bots
# (e.g. Claude Code's default committer) get explicit entries below.
BOT_NAME_PATTERN = re.compile(r"\[bot\]$", re.IGNORECASE)
EXCLUDED_NAMES: set[str] = {
    "Claude",  # claude.ai / Claude Code default committer name
}
EXCLUDED_EMAILS: set[str] = {
    "noreply@anthropic.com",  # backstop in case the name varies
}


def is_bot(name: str, email: str) -> bool:
    """True if this author identity should be excluded from CONTRIBUTORS.md."""
    if BOT_NAME_PATTERN.search(name):
        return True
    if name in EXCLUDED_NAMES or email in EXCLUDED_EMAILS:
        return True
    return False


def get_contributors() -> list[str]:
    """Get a list of contributors from git log, excluding known bot identities."""
    # Using appropriate git command based on platform
    git_cmd = "git"  # Default command
    result = subprocess.run(
        [git_cmd, "log", "--format=%aN <%aE>"],
        capture_output=True,
        text=True,
        check=True,
    )

    # Get unique contributors, filtering out bots.
    contributors: set[str] = set()
    for raw_line in result.stdout.strip().split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # Parse "Name <email>" — name may contain spaces; email is everything
        # inside the final <...>.
        name, _, rest = line.partition(" <")
        email = rest.rstrip(">")
        if is_bot(name, email):
            continue
        contributors.add(line)

    # Sort contributors alphabetically
    return sorted(contributors)


def update_contributors_file(contributors: list[str]) -> None:
    """Update the CONTRIBUTORS.md file with the list of contributors"""
    with open("CONTRIBUTORS.md") as f:
        content = f.read()

    # Create the new contributors section
    contributors_section = "\n".join(contributors)

    # Update the content between the start and end markers
    pattern = (
        r"(<!-- COG-CONTRIBUTORS-LIST:START -->).*"
        r"(<!-- COG-CONTRIBUTORS-LIST:END -->)"
    )
    replacement = r"\1\n" + contributors_section + r"\n\2"
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open("CONTRIBUTORS.md", "w") as f:
        f.write(updated_content)


def main() -> None:
    contributors = get_contributors()
    update_contributors_file(contributors)
    print(f"Updated CONTRIBUTORS.md with {len(contributors)} contributors")


if __name__ == "__main__":
    main()
