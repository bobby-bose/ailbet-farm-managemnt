#!/bin/bash

# Initialize a new Git repository (only if not already initialized)

git init


# Add all files to staging
git add .

# Commit changes with a default message
git commit -m "first commit"

# Set the branch to main
git branch -M main

# Add the remote origin if it’s not already set
git remote set-url origin https://github_pat_11ANTHFGY01G7z78adFAwj_ZVJKSmF9AVR92lJE@github.com/bobby-bose/ailbet-farm-managemnt.git
git remote add origin https://github.com/bobby-bose/ailbet-farm-managemnt.git

# Push to the remote repository
git push -u origin main
