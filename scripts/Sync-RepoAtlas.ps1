param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$Bookmarks
)

$ErrorActionPreference = 'Stop'

$GhCommand = Get-Command gh -ErrorAction SilentlyContinue
$HasEnvToken = -not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN) -or -not [string]::IsNullOrWhiteSpace($env:GH_TOKEN)
if (-not $GhCommand -and -not $HasEnvToken) {
    throw 'GitHub CLI não encontrado e nenhum GITHUB_TOKEN/ GH_TOKEN definido. Instale com: winget install --id GitHub.cli'
}

if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.11+ não encontrado. Instale Python e tente novamente.'
}

if (-not (Test-Path '.venv')) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    } else {
        python -m venv .venv
    }
}

$Python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $Python -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar RepoAtlas.' }

if (-not $HasEnvToken) {
    & gh auth status
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Autenticação ausente. Abrindo o fluxo de login do GitHub CLI...'
        & gh auth login
        if ($LASTEXITCODE -ne 0) { throw 'Falha na autenticação do GitHub CLI.' }
    }
}

& $Python -m repoatlas sync --bookmarks $Bookmarks --github --output '.repoatlas'
if ($LASTEXITCODE -ne 0) { throw 'Falha na sincronização RepoAtlas.' }

$Dashboard = Join-Path (Get-Location) '.repoatlas\dashboard.html'
Start-Process $Dashboard
Write-Host "Dashboard aberto: $Dashboard"
