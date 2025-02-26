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
