# Force kill all processes related to Otium
Write-Host "========================================"
Write-Host "FORCE KILL ALL OTIUM PROCESSES"
Write-Host "========================================"
Write-Host ""

# 1. Kill all processes on port 8000
Write-Host "[1] Killing all processes on port 8000..."
$port8000Connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000Connections) {
    foreach ($conn in $port8000Connections) {
        $procId = $conn.OwningProcess
        if ($procId -gt 0) {
            try {
                Write-Host "  Killing PID: $procId (State: $($conn.State))"
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "  Successfully killed PID: $procId"
            } catch {
                Write-Host "  Failed to kill PID: $procId ($($_.Exception.Message))"
            }
        }
    }
} else {
    Write-Host "  No processes found on port 8000"
}

# 2. Kill all processes on port 3000
Write-Host ""
Write-Host "[2] Killing all processes on port 3000..."
$port3000Connections = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000Connections) {
    foreach ($conn in $port3000Connections) {
        $procId = $conn.OwningProcess
        if ($procId -gt 0) {
            try {
                Write-Host "  Killing PID: $procId (State: $($conn.State))"
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "  Successfully killed PID: $procId"
            } catch {
                Write-Host "  Failed to kill PID: $procId ($($_.Exception.Message))"
            }
        }
    }
} else {
    Write-Host "  No processes found on port 3000"
}

# 3. Kill all Node.js processes
Write-Host ""
Write-Host "[3] Killing all Node.js processes..."
$nodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    foreach ($process in $nodeProcesses) {
        try {
            Write-Host "  Killing Node process: $($process.Id)"
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Write-Host "  Successfully killed Node process: $($process.Id)"
        } catch {
            Write-Host "  Failed to kill Node process: $($process.Id) ($($_.Exception.Message))"
        }
    }
} else {
    Write-Host "  No Node.js processes found"
}

# 4. Kill all Python processes
Write-Host ""
Write-Host "[4] Killing all Python processes..."
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    foreach ($process in $pythonProcesses) {
        try {
            Write-Host "  Killing Python process: $($process.Id)"
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Write-Host "  Successfully killed Python process: $($process.Id)"
        } catch {
            Write-Host "  Failed to kill Python process: $($process.Id) ($($_.Exception.Message))"
        }
    }
} else {
    Write-Host "  No Python processes found"
}

# 5. Wait and check
Write-Host ""
Write-Host "[5] Waiting 2 seconds for processes to fully terminate..."
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[6] Final port check:"
$final8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$final3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($final8000) {
    Write-Host "  WARNING: Port 8000 still in use!"
    $final8000 | Format-Table LocalPort, OwningProcess, State -AutoSize
} else {
    Write-Host "  Port 8000 is free"
}

if ($final3000) {
    Write-Host "  WARNING: Port 3000 still in use!"
    $final3000 | Format-Table LocalPort, OwningProcess, State -AutoSize
} else {
    Write-Host "  Port 3000 is free"
}

Write-Host ""
Write-Host "========================================"
Write-Host "PROCESS KILL COMPLETE!"
Write-Host "========================================"