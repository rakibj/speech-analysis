$headers = @{
    'X-RapidAPI-Key' = 'sk_wpUwYgv2RMtAhwTecCh0Qfp9'
    'X-RapidAPI-Signature' = '6fa32cf82f61b2ea93f75a79098898f85f5abd95ed807da586124effc2dd7f23'
    'X-RapidAPI-Host' = 'localhost:8000'
}

Write-Host "Testing /api/v1/health endpoint..."
Write-Host "Headers:"
foreach ($key in $headers.Keys) {
    Write-Host "  $key : $($headers[$key])"
}

try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/v1/health' -Headers $headers -ErrorAction Stop
    Write-Host "`nStatus: $($response.StatusCode)"
    Write-Host "Response:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10 | Write-Host
} catch {
    Write-Host "`n[ERROR] $($_.Exception.Message)"
}
