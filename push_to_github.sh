#!/bin/bash
# Push AIRP to GitHub
# Usage: ./push_to_github.sh <github-username> <repository-name>

if [ $# -lt 2 ]; then
    echo "Usage: ./push_to_github.sh <github-username> <repository-name>"
    echo "Example: ./push_to_github.sh yourusername AIRP"
    exit 1
fi

GITHUB_USER=$1
REPO_NAME=$2
GITHUB_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo "=========================================="
echo "Pushing AIRP to GitHub"
echo "=========================================="
echo "Repository URL: $GITHUB_URL"
echo ""

cd "$(dirname "$0")"

# Add remote origin
echo "Adding GitHub remote..."
git remote add origin $GITHUB_URL

# Set default branch to main
git branch -M main

# Push to GitHub
echo "Pushing to GitHub (main branch)..."
git push -u origin main

echo ""
echo "=========================================="
echo "✓ Successfully pushed to GitHub!"
echo "=========================================="
echo "Repository: $GITHUB_URL"
