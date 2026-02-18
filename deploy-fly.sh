#!/bin/bash

# EventFlow Fly.io Deployment Script
# This script automates the deployment process

set -e

echo "🚀 EventFlow Fly.io Deployment Script"
echo "======================================"
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed"
    echo "Install it with: brew install flyctl (macOS) or curl -L https://fly.io/install.sh | sh (Linux)"
    exit 1
fi

echo "✅ flyctl is installed"

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io"
    echo "Run: flyctl auth login"
    exit 1
fi

echo "✅ Logged in to Fly.io"
echo ""

# Step 1: Create PostgreSQL
echo "📦 Step 1: Setting up PostgreSQL"
echo "================================"
read -p "Create new PostgreSQL database? (y/n): " create_db

if [ "$create_db" = "y" ]; then
    echo "Creating PostgreSQL cluster..."
    flyctl postgres create --name eventflow-db --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1
    echo ""
    echo "⚠️  IMPORTANT: Save the connection string shown above!"
    echo "Press Enter when you've saved it..."
    read
fi

# Step 2: Get connection details
echo ""
echo "📝 Step 2: Configuration"
echo "======================="
read -p "Enter PostgreSQL connection string (postgres://...): " db_url
read -p "Enter Redis URL from Upstash (redis://...): " redis_url

# Step 3: Deploy API
echo ""
echo "🌐 Step 3: Deploying API Service"
echo "================================"

# Check if app exists
if flyctl apps list | grep -q "eventflow-api"; then
    echo "App eventflow-api already exists, updating..."
else
    echo "Creating eventflow-api app..."
    flyctl apps create eventflow-api --org personal
fi

echo "Setting secrets for API..."
flyctl secrets set \
  DATABASE_URL="$db_url" \
  REDIS_URL="$redis_url" \
  -a eventflow-api

echo "Deploying API..."
flyctl deploy -c fly.toml

echo "✅ API deployed successfully!"

# Step 4: Initialize Database
echo ""
echo "🗄️  Step 4: Initialize Database"
echo "=============================="
read -p "Initialize database schema? (y/n): " init_db

if [ "$init_db" = "y" ]; then
    echo "Connecting to database..."
    echo "Please run the following SQL commands:"
    echo ""
    cat scripts/init_db.sql
    echo ""
    echo "Opening database connection..."
    flyctl postgres connect -a eventflow-db
fi

# Step 5: Deploy Worker
echo ""
echo "⚙️  Step 5: Deploying Worker Service"
echo "==================================="

# Check if app exists
if flyctl apps list | grep -q "eventflow-worker"; then
    echo "App eventflow-worker already exists, updating..."
else
    echo "Creating eventflow-worker app..."
    flyctl apps create eventflow-worker --org personal
fi

echo "Setting secrets for Worker..."
flyctl secrets set \
  DATABASE_URL="$db_url" \
  REDIS_URL="$redis_url" \
  -a eventflow-worker

echo "Deploying Worker..."
flyctl deploy -c fly.worker.toml

echo "✅ Worker deployed successfully!"

# Step 6: Test deployment
echo ""
echo "🧪 Step 6: Testing Deployment"
echo "============================="

API_URL=$(flyctl info -a eventflow-api --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)

if [ -z "$API_URL" ]; then
    echo "⚠️  Could not get API URL automatically"
    echo "Run: flyctl info -a eventflow-api"
else
    echo "API URL: https://$API_URL"
    echo ""
    echo "Testing health endpoint..."
    
    if curl -s "https://$API_URL/health" | grep -q "healthy"; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed, check logs with: flyctl logs -a eventflow-api"
    fi
fi

# Summary
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "Your EventFlow system is now running on Fly.io (FREE tier)!"
echo ""
echo "📍 API URL: https://$API_URL"
echo "📚 API Docs: https://$API_URL/docs"
echo "🏥 Health Check: https://$API_URL/health"
echo ""
echo "Useful commands:"
echo "  flyctl logs -a eventflow-api      # View API logs"
echo "  flyctl logs -a eventflow-worker   # View worker logs"
echo "  flyctl status -a eventflow-api    # Check API status"
echo "  flyctl ssh console -a eventflow-api  # SSH into API"
echo ""
echo "Test your API:"
echo "  curl https://$API_URL/health"
echo ""
echo "Send a test event:"
echo "  curl -X POST https://$API_URL/events \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"event_type\":\"purchase\",\"user_id\":\"test\",\"properties\":{\"amount\":99.99}}'"
echo ""
echo "Happy event processing! 🚀"
