[CmdletBinding()]
param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [string]$Title,
    [string]$InputFile,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$postDir = Join-Path $repoRoot "content\posts"
$postPath = Join-Path $postDir "$Date.md"

if (Test-Path -LiteralPath $postPath) {
    throw "Post already exists: $postPath"
}

if ($InputFile) {
    $raw = Get-Content -LiteralPath $InputFile -Raw
} else {
    $raw = Get-Clipboard -Raw
}

if ([string]::IsNullOrWhiteSpace($raw)) {
    throw "No post text found. Copy the ChatGPT Markdown response first, or pass -InputFile."
}

function Clean-PostMarkdown {
    param([string]$Text)

    $clean = $Text
    $clean = $clean -replace '(?s):contentReference\[[^\]]*\]\{[^}]*\}', ''
    $clean = $clean -replace '(?s)&#8203;:contentReference\[[^\]]*\]\{[^}]*\}', ''
    $clean = $clean -replace '(?s):contentReference\[[^\]]*\]', ''
    $clean = $clean -replace '&#8203;', ''
    $clean = $clean -replace '\u200B', ''
    $clean = $clean -replace '\boaicite:\d+\b', ''
    $clean = $clean -replace '^\s*```(?:markdown|md)?\s*', ''
    $clean = $clean -replace '\s*```\s*$', ''
    $clean = $clean -replace "`r`n", "`n"
    $clean = $clean -replace "`r", "`n"
    $clean = $clean -replace "`n{4,}", "`n`n`n"

    return $clean.Trim()
}

function Get-DefaultTitle {
    param([string]$PostDate)

    $parsed = [DateTime]::ParseExact($PostDate, "yyyy-MM-dd", $null)
    return "AI & Labor Watch: $($parsed.ToString('MMMM d, yyyy')) - Automation and Labor Signals"
}

$body = Clean-PostMarkdown $raw

if ($body -notmatch '(?s)^---\s*\n.*?\n---') {
    if (-not $Title) {
        $heading = [regex]::Match($body, '(?m)^#\s+(.+)$')
        if ($heading.Success) {
            $Title = $heading.Groups[1].Value.Trim()
            $body = ($body -replace '(?m)^#\s+.+\n?', '').Trim()
        } else {
            $Title = Get-DefaultTitle $Date
        }
    }

    $frontMatter = @"
---
title: "$Title"
date: $Date
draft: false
---

"@
    $body = $frontMatter + $body
}

$badPatterns = @(
    ':contentReference',
    'oaicite',
    '[Link here]',
    ']()'
)

foreach ($pattern in $badPatterns) {
    if ($body.Contains($pattern)) {
        throw "Cleaned post still contains suspicious text: $pattern"
    }
}

New-Item -ItemType Directory -Force -Path $postDir | Out-Null
Set-Content -LiteralPath $postPath -Value $body -Encoding utf8NoBOM

Write-Host "Created $postPath"

if (-not $NoBuild) {
    Push-Location $repoRoot
    try {
        hugo
    } finally {
        Pop-Location
    }
}
