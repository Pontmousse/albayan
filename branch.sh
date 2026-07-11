#!/usr/bin/env bash

# branch.sh — Same as push.sh, but on a non-main feature branch.
# Usage:
#   ./branch.sh feature-branch-name "commit message"
#   ./branch.sh feature-branch-name

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
REMOTE="origin"
PROTECTED_BRANCHES=("main" "master")

if [ $# -lt 1 ]; then
    echo -e "${RED}Usage:${RESET} ./branch.sh <branch-name> [commit message]"
    echo "Example: ./branch.sh feature/invitations \"Add invitation flow\""
    exit 1
fi

TARGET_BRANCH="$1"
shift
MESSAGE="${*:-$DEFAULT_MESSAGE}"

for protected in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$TARGET_BRANCH" = "$protected" ]; then
        echo -e "${RED}Error: cannot use branch.sh on '$protected'.${RESET}"
        echo "Use ./push.sh for the main branch, or choose another branch name."
        exit 1
    fi
done

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
echo -e "${CYAN}Starting branch push process...${RESET}"
echo ""

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}Error: this folder is not a Git repository.${RESET}"
    exit 1
fi

CURRENT_BRANCH="$(git branch --show-current)"

echo -e "${CYAN}Current branch:${RESET} $CURRENT_BRANCH"
echo -e "${CYAN}Target branch:${RESET} $TARGET_BRANCH"
echo -e "${CYAN}Commit message:${RESET} $MESSAGE"
echo ""

if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
    if git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
        echo -e "${YELLOW}Switching to existing branch '$TARGET_BRANCH'...${RESET}"
        git checkout "$TARGET_BRANCH"
    elif git show-ref --verify --quiet "refs/remotes/$REMOTE/$TARGET_BRANCH"; then
        echo -e "${YELLOW}Checking out remote branch '$TARGET_BRANCH'...${RESET}"
        git checkout -b "$TARGET_BRANCH" --track "$REMOTE/$TARGET_BRANCH"
    else
        echo -e "${YELLOW}Creating and switching to new branch '$TARGET_BRANCH'...${RESET}"
        git checkout -b "$TARGET_BRANCH"
    fi
    echo -e "${GREEN}Now on branch '$TARGET_BRANCH'.${RESET}"
    echo ""
fi

BRANCH="$(git branch --show-current)"

if [ "$BRANCH" != "$TARGET_BRANCH" ]; then
    echo -e "${RED}Error: failed to switch to '$TARGET_BRANCH' (still on '$BRANCH').${RESET}"
    exit 1
fi

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
        echo -e "${YELLOW}No upstream branch set. Pushing with -u...${RESET}"
        if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
            echo -e "${RED}Error: remote '$REMOTE' is not configured.${RESET}"
            echo "Add it first using:"
            echo "  git remote add origin YOUR_REPOSITORY_URL"
            exit 1
        fi
        git --no-pager push -u "$REMOTE" "$BRANCH"
        echo -e "${GREEN}Push completed successfully.${RESET}"
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
