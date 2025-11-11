#!/bin/bash
# Complete ETL workflow: fetch data → insert → commit → push
#
# This script:
# 1. Runs the Python ETL to fetch and insert data
# 2. Uses Dolt CLI to add, commit, and push changes
#
# Usage:
#   ./etl/run_etl_and_push.sh

set -e  # Exit on error

cd "$(dirname "$0")/.."  # Go to project root

echo ""
echo "🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷"
echo "   COMPLETE ETL WORKFLOW: FETCH → INSERT → COMMIT → PUSH"
echo "🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷🇦🇷"
echo ""

# Step 1: Run Python ETL
echo "📊 Step 1: Running Python ETL..."
echo "="*70
source .venv/bin/activate
python etl/populate_usd_uva.py

if [ $? -ne 0 ]; then
    echo "❌ ETL failed. Aborting."
    exit 1
fi

echo ""
echo "✅ ETL completed successfully!"
echo ""

# Step 2: Add changes to Dolt
echo "📝 Step 2: Adding changes to Dolt..."
echo "="*70
dolt add fx_rate

echo ""
echo "✅ Changes staged"
echo ""

# Step 3: Commit changes
echo "💾 Step 3: Committing changes..."
echo "="*70

COMMIT_MSG="ETL update $(date '+%Y-%m-%d %H:%M')"
dolt commit -m "$COMMIT_MSG"

if [ $? -ne 0 ]; then
    echo "⚠️  Nothing to commit (no changes detected)"
else
    echo "✅ Committed: $COMMIT_MSG"
fi

echo ""

# Step 4: Push to DoltHub
echo "🚀 Step 4: Pushing to DoltHub..."
echo "="*70

read -p "Push to DoltHub remote? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    dolt push origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Pushed to DoltHub successfully!"
    else
        echo "❌ Push failed. You may need to configure credentials."
        echo "   See: DOLTHUB_CREDENTIALS_GUIDE.md"
        exit 1
    fi
else
    echo "⏸️  Push skipped. Run manually when ready:"
    echo "   dolt push origin main"
fi

echo ""
echo "="*70
echo "✅ WORKFLOW COMPLETED!"
echo "="*70
echo ""
echo "📊 View your data at:"
echo "   https://www.dolthub.com/repositories/rbasa/macroeconomia"
echo ""

