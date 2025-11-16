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


def get_contributors() -> list[str]:
    """Get a list of contributors from git log"""
    # Using appropriate git command based on platform
    git_cmd = "git"  # Default command
    result = subprocess.run(
        [git_cmd, "log", "--format=%aN <%aE>"],
        capture_output=True,
        text=True,
        check=True,
    )

    # Get unique contributors
    contributors: set[str] = set()
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            contributors.add(line.strip())

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
