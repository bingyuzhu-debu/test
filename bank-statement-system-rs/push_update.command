#!/bin/bash
cd "$(dirname "$0")"
echo "Starting update..."
git add .
git commit -m "Update from one-click script"
git push
echo "---------------------------------------------------"
echo "Success! Code pushed to GitHub."
echo "Please go to GitHub Actions to check the build status."
echo "---------------------------------------------------"
