param(
  [Parameter(Mandatory = $false)]
  [string]$Mode = "none"
)

$env:VICTIM_PROTECTION = $Mode
python .\victim\app.py


