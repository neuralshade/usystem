param(
    [ValidateSet("build", "watch", "icons")]
    [string]$Mode = "build"
)

$npmCommand = switch ($Mode) {
    "watch" { "frontend:watch" }
    "icons" { "icons:prepare" }
    default { "frontend:build" }
}

Write-Host ""
Write-Host "USystem frontend pipeline" -ForegroundColor Cyan
Write-Host "Executando npm run $npmCommand" -ForegroundColor DarkGray
Write-Host ""

npm run $npmCommand
