# Powershell activation script
function global:_old_virtual_prompt {
""
}
$function:_old_virtual_prompt = $function:prompt
function global:prompt {
    $previous_prompt_value = & $function:_old_virtual_prompt
    ("(" + $env:PYTUI_VIRTUAL_ENV_PROMPT + ") " + $previous_prompt_value)
}
function deactivate {
    Exit 0
}

# Set the new environment variables from the PYTUI versions.
$env:PATH = $env:PYTUI_PATH
$env:VIRTUAL_ENV = $env:PYTUI_VIRTUAL_ENV
$env:VIRTUAL_ENV_PROMPT = $env:PYTUI_VIRTUAL_ENV_PROMPT
$env:PYTHONHOME = $null
