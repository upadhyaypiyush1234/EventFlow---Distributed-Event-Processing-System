# Send a test event to EventFlow using PowerShell
# No Python required!

Write-Host "🚀 Sending test event to EventFlow..." -ForegroundColor Cyan
Write-Host ""

# Create event data
$event = @{
    event_type = "purchase"
    user_id = "user_$(Get-Random -Minimum 1 -Maximum 1000)"
    properties = @{
        amount = [math]::Round((Get-Random -Minimum 10 -Maximum 1000) + (Get-Random) / 100, 2)
        product_id = "prod_$(Get-Random -Minimum 1000 -Maximum 9999)"
        currency = "USD"
    }
} | ConvertTo-Json

Write-Host "Event data:" -ForegroundColor Yellow
Write-Host $event
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/events" -Method Post -Body $event -ContentType "application/json"
    
    Write-Host "✅ Event sent successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    Write-Host "  Event ID: $($response.event_id)" -ForegroundColor White
    Write-Host "  Status:   $($response.status)" -ForegroundColor White
    Write-Host "  Message:  $($response.message)" -ForegroundColor White
    Write-Host ""
    
    # Check metrics
    Write-Host "📊 Checking metrics..." -ForegroundColor Cyan
    $metrics = Invoke-RestMethod -Uri "http://localhost:8000/metrics/summary"
    Write-Host "  Queue Length:     $($metrics.queue_length)" -ForegroundColor White
    Write-Host "  Pending Messages: $($metrics.pending_messages)" -ForegroundColor White
}
catch {
    Write-Host "❌ Failed to send event" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Make sure EventFlow is running:" -ForegroundColor White
    Write-Host "  docker-compose up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "Check health:" -ForegroundColor White
    Write-Host "  curl http://localhost:8000/health" -ForegroundColor White
}

Write-Host ""
Write-Host "💡 Tip: Open http://localhost:8000/docs to use the interactive API" -ForegroundColor Cyan
