#!/usr/bin/env bash

# push.sh — Simple Git add, commit, and push script.
# Usage:
#   ./push.sh "commit message"
#   ./push.sh

set -euo pipefail

export GIT_PAGER=cat
export PAGER=cat

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
RESET="\033[0m"

DEFAULT_MESSAGE="Update database project"
MESSAGE="${*:-$DEFAULT_MESSAGE}"

REMOTE="origin"

block_sensitive_files() {
    local blocked=""

    while IFS= read -r file; do
        [ -z "$file" ] && continue

        lower_file="${file,,}"

        # Allow example/template files, such as:
        # .env.example
        # .env.local.example
        # backend/.env.production.example
        if [[ "$lower_file" == *example* ]]; then
            continue
        fi

        case "$file" in
            .env|*/.env|.env.*|*/.env.*|*.pem|*keyless.json*)
                blocked="${blocked}  - ${file}\n"
                ;;
        esac
    done < <(git diff --cached --name-only)

    if [ -n "$blocked" ]; then
        echo -e "${RED}Blocked: sensitive files are staged:${RESET}"
        echo -e "$blocked"
        echo "Please unstage these files or add them to .gitignore before pushing."
        exit 1
    fi
}

echo ""
echo -e "${CYAN}Starting push process...${RESET}"
echo ""

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}Error: this folder is not a Git repository.${RESET}"
    exit 1
fi

BRANCH="$(git branch --show-current)"

echo -e "${CYAN}Branch:${RESET} $BRANCH"
echo -e "${CYAN}Commit message:${RESET} $MESSAGE"
echo ""

echo -e "${YELLOW}Staging changes...${RESET}"
git add -A
block_sensitive_files

if git diff --cached --quiet; then
    echo -e "${GREEN}No changes to commit.${RESET}"

    if git rev-parse --abbrev-ref "@{u}" >/dev/null 2>&1; then
        AHEAD="$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo 0)"

        if [ "$AHEAD" -gt 0 ]; then
            echo -e "${YELLOW}You have $AHEAD unpushed commit(s). Pushing now...${RESET}"
            git --no-pager push
            echo -e "${GREEN}Push completed successfully.${RESET}"
        else
            echo -e "${GREEN}Everything is already up to date.${RESET}"
        fi
    else
        echo -e "${YELLOW}No upstream branch set. Nothing to push.${RESET}"
    fi

    exit 0
fi

echo -e "${GREEN}Changes staged.${RESET}"
git --no-pager diff --cached --shortstat || true
echo ""

echo -e "${YELLOW}Creating commit...${RESET}"
git commit -m "$MESSAGE"
echo -e "${GREEN}Commit created.${RESET}"
echo ""

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
    echo -e "${RED}Error: remote '$REMOTE' is not configured.${RESET}"
    echo "Add it first using:"
    echo "  git remote add origin YOUR_REPOSITORY_URL"
    exit 1
fi

echo -e "${YELLOW}Pushing to GitHub...${RESET}"

if git rev-parse --abbrev-ref "@{u}" >/dev/null 2>&1; then
    git --no-pager push
else
    git --no-pager push -u "$REMOTE" "$BRANCH"
fi

echo ""
echo -e "${GREEN}Done. Changes pushed successfully to $REMOTE/$BRANCH.${RESET}"
echo ""