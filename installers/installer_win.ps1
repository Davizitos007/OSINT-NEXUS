# OSINT-Nexus Windows Installer
# Run as Administrator: powershell -ExecutionPolicy Bypass -File installer_win.ps1

param(
    [switch]$Uninstall,
    [string]$InstallPath = "C:\Program Files\OSINT-Nexus"
)

$AppName = "OSINT-Nexus"
$ExeName = "osint-nexus.exe"
$IconName = "app_icon.ico"
$ShortcutName = "OSINT-Nexus.lnk"
$StartMenuFolder = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\OSINT-Nexus"
$DesktopShortcut = "$env:USERPROFILE\Desktop\$ShortcutName"

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║           OSINT-Nexus Installer           ║" -ForegroundColor Cyan
    Write-Host "  ║   Cross-Platform OSINT Gathering Tool     ║" -ForegroundColor Cyan
    Write-Host "  ╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Application {
    Write-Banner
    Write-Host "[*] Starting installation..." -ForegroundColor Green
    
    # Check for admin rights
    if (-not (Test-Administrator)) {
        Write-Host "[!] Warning: Not running as Administrator." -ForegroundColor Yellow
        Write-Host "    Some features may require elevated privileges." -ForegroundColor Yellow
        Write-Host ""
    }
    
    # Create installation directory
    Write-Host "[*] Creating installation directory..." -ForegroundColor Cyan
    if (-not (Test-Path $InstallPath)) {
        try {
            New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
            Write-Host "    Created: $InstallPath" -ForegroundColor Green
        } catch {
            Write-Host "[!] Failed to create directory. Try running as Administrator." -ForegroundColor Red
            exit 1
        }
    }
    
    # Copy application files
    Write-Host "[*] Copying application files..." -ForegroundColor Cyan
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $DistDir = Join-Path (Split-Path -Parent $ScriptDir) "dist"
    
    if (Test-Path "$DistDir\$ExeName") {
        Copy-Item "$DistDir\$ExeName" "$InstallPath\$ExeName" -Force
        Write-Host "    Copied: $ExeName" -ForegroundColor Green
    } else {
        Write-Host "[!] Executable not found in $DistDir" -ForegroundColor Yellow
        Write-Host "    Please run PyInstaller first: pyinstaller build.spec" -ForegroundColor Yellow
    }
    
    # Copy assets
    $AssetsDir = Join-Path (Split-Path -Parent $ScriptDir) "assets"
    if (Test-Path $AssetsDir) {
        Copy-Item -Path $AssetsDir -Destination "$InstallPath\assets" -Recurse -Force
        Write-Host "    Copied: assets/" -ForegroundColor Green
    }
    
    # Create Start Menu folder and shortcut
    Write-Host "[*] Creating Start Menu entry..." -ForegroundColor Cyan
    try {
        if (-not (Test-Path $StartMenuFolder)) {
            New-Item -ItemType Directory -Path $StartMenuFolder -Force | Out-Null
        }
        
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$StartMenuFolder\$ShortcutName")
        $Shortcut.TargetPath = "$InstallPath\$ExeName"
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.Description = "OSINT Gathering and Visualization Tool"
        
        if (Test-Path "$InstallPath\assets\$IconName") {
            $Shortcut.IconLocation = "$InstallPath\assets\$IconName"
        }
        
        $Shortcut.Save()
        Write-Host "    Created: Start Menu shortcut" -ForegroundColor Green
    } catch {
        Write-Host "[!] Failed to create Start Menu shortcut" -ForegroundColor Yellow
    }
    
    # Create Desktop shortcut
    Write-Host "[*] Creating Desktop shortcut..." -ForegroundColor Cyan
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($DesktopShortcut)
        $Shortcut.TargetPath = "$InstallPath\$ExeName"
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.Description = "OSINT Gathering and Visualization Tool"
        
        if (Test-Path "$InstallPath\assets\$IconName") {
            $Shortcut.IconLocation = "$InstallPath\assets\$IconName"
        }
        
        $Shortcut.Save()
        Write-Host "    Created: Desktop shortcut" -ForegroundColor Green
    } catch {
        Write-Host "[!] Failed to create Desktop shortcut" -ForegroundColor Yellow
    }
    
    # Add to PATH (optional)
    Write-Host "[*] Adding to system PATH..." -ForegroundColor Cyan
    try {
        $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($CurrentPath -notlike "*$InstallPath*") {
            [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$InstallPath", "Machine")
            Write-Host "    Added to PATH" -ForegroundColor Green
        } else {
            Write-Host "    Already in PATH" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[!] Failed to update PATH (requires Administrator)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "══════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host " Installation Complete!" -ForegroundColor Green
    Write-Host "══════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host " Location: $InstallPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " Launch from:" -ForegroundColor White
    Write-Host "   • Desktop shortcut" -ForegroundColor Gray
    Write-Host "   • Start Menu > OSINT-Nexus" -ForegroundColor Gray
    Write-Host "   • Command line: osint-nexus" -ForegroundColor Gray
    Write-Host ""
}

function Uninstall-Application {
    Write-Banner
    Write-Host "[*] Starting uninstallation..." -ForegroundColor Yellow
    
    # Remove installation directory
    if (Test-Path $InstallPath) {
        Remove-Item -Path $InstallPath -Recurse -Force
        Write-Host "    Removed: $InstallPath" -ForegroundColor Green
    }
    
    # Remove Start Menu folder
    if (Test-Path $StartMenuFolder) {
        Remove-Item -Path $StartMenuFolder -Recurse -Force
        Write-Host "    Removed: Start Menu entry" -ForegroundColor Green
    }
    
    # Remove Desktop shortcut
    if (Test-Path $DesktopShortcut) {
        Remove-Item -Path $DesktopShortcut -Force
        Write-Host "    Removed: Desktop shortcut" -ForegroundColor Green
    }
    
    # Remove from PATH
    try {
        $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $NewPath = ($CurrentPath -split ";" | Where-Object { $_ -ne $InstallPath }) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "Machine")
        Write-Host "    Removed from PATH" -ForegroundColor Green
    } catch {
        Write-Host "[!] Failed to update PATH" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Uninstallation complete!" -ForegroundColor Green
    Write-Host ""
}

# Main execution
if ($Uninstall) {
    Uninstall-Application
} else {
    Install-Application
}
