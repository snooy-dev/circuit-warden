# Dot-source this file to expose project-local tools in this process only.
$projectToolRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../.local-tools'))
$projectPythonScripts = Join-Path $projectToolRoot 'python/Scripts'
if (-not (Test-Path -LiteralPath (Join-Path $projectPythonScripts 'specify.exe'))) {
    throw 'Project tools are missing. See docs/tooling.md.'
}
$env:PATH = (@($projectPythonScripts, $env:PATH) -join ';')
$env:SPECKIT_PYTHON_EXECUTABLE = Join-Path $projectPythonScripts 'python.exe'
$env:PIXELFX_DIR = Join-Path $projectToolRoot 'pixelfx'
$env:PYTHONUTF8 = '1'
