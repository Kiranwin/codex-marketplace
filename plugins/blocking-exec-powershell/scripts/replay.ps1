param(
    [Parameter(Mandatory = $true)]
    [string]$Result
)

$ErrorActionPreference = 'Stop'
$separator = $Result.IndexOf('|')
if ($separator -lt 1) {
    [Console]::Error.WriteLine('blocking-exec: invalid replay arguments')
    exit 2
}

$status = [int]$Result.Substring(0, $separator)
$logPath = $Result.Substring($separator + 1)
try {
    $bytes = [System.IO.File]::ReadAllBytes($logPath)
    $output = [Console]::OpenStandardOutput()
    $output.Write($bytes, 0, $bytes.Length)
    $output.Flush()
}
catch {
    [Console]::Error.WriteLine("blocking-exec: cannot read captured output: $($_.Exception.Message)")
    exit 127
}
exit $status
