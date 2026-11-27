param([Parameter(Mandatory=$true)][int]$ServerId,
      [Parameter(Mandatory=$true)][string]$Destination)
# Windows exposes per-process engine runtime in 100 ns units and allocation sizes in bytes.
# https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/
$ErrorActionPreference = 'Stop'
$server = Get-Process -Id $ServerId -ErrorAction SilentlyContinue
if (-not $server) {exit}
$created = $server.StartTime
while (($server = Get-Process -Id $ServerId -ErrorAction SilentlyContinue) -and $server.StartTime -eq $created) {
    $selector = "Name LIKE 'pid_${ServerId}_%'"
    $engines = @(Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUEngine -Filter $selector |
        Where-Object RunningTime -gt 0 | ForEach-Object {
            [ordered]@{engine=$_.Name.Split('_')[-1];seconds=[double]$_.RunningTime/$_.Frequency_Sys100NS}
        })
    $memory = @(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory -Filter $selector)
    if ($engines.Count -and $memory.Count) {
        $record = [ordered]@{time=(Get-Date).ToUniversalTime().ToString('o');pid=$ServerId;engines=$engines
            dedicated_bytes=($memory|Measure-Object DedicatedUsage -Sum).Sum
            shared_bytes=($memory|Measure-Object SharedUsage -Sum).Sum}
        [IO.File]::AppendAllText($Destination,($record|ConvertTo-Json -Compress -Depth 4)+[Environment]::NewLine,
            [Text.UTF8Encoding]::new($false))
    }
    Start-Sleep -Seconds 5
}
