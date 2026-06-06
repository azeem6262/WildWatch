param (
    [switch]$BuildBackend = $true,
    [switch]$BuildFrontend = $true
)

$ErrorActionPreference = "Stop"

if ($BuildBackend) {
    Write-Host "=========================================="
    Write-Host "1. Building Python Backend with PyInstaller"
    Write-Host "=========================================="
    
    # Run PyInstaller with --onefile so Tauri can use it as a sidecar
    pyinstaller --name wildwatch_backend --noconfirm --clean --onefile `
        --add-data "models/clip-vit-base-patch32;models/clip-vit-base-patch32" `
        --hidden-import=ultralytics `
        --hidden-import=speciesnet `
        --hidden-import=transformers `
        --hidden-import=torch `
        --hidden-import=uvicorn.logging `
        --hidden-import=uvicorn.loops `
        --hidden-import=uvicorn.loops.auto `
        --hidden-import=uvicorn.protocols `
        --hidden-import=uvicorn.protocols.http `
        --hidden-import=uvicorn.protocols.http.auto `
        --hidden-import=uvicorn.protocols.websockets `
        --hidden-import=uvicorn.protocols.websockets.auto `
        --hidden-import=uvicorn.lifespan `
        --hidden-import=uvicorn.lifespan.on `
        --hidden-import=uvicorn.lifespan.off `
        backend/main.py
    
    # Create bin directory for Tauri sidecar
    New-Item -ItemType Directory -Force -Path "app/src-tauri/bin" | Out-Null
    
    # Tauri expects sidecars to have the target triple suffix (e.g., -x86_64-pc-windows-msvc)
    # We copy the built executable to the expected location
    Copy-Item "dist/wildwatch_backend.exe" -Destination "app/src-tauri/bin/backend-x86_64-pc-windows-msvc.exe" -Force
    
    Write-Host "Backend built and copied to sidecar directory successfully."
}

if ($BuildFrontend) {
    Write-Host "=========================================="
    Write-Host "2. Building Tauri Application Installer"
    Write-Host "=========================================="
    
    cd app
    npm install
    npm run tauri build
    
    Write-Host "Tauri build completed!"
}

Write-Host "=========================================="
Write-Host "Release build process finished."
Write-Host "=========================================="
