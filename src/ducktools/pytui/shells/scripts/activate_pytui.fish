# Much of this is based on or copied from the
# regular 'venv' activate script
# But without the backup/restore functionality

# Unlike BASH, fish will launch with all of its normal config
# Before running this script
alias deactivate="exit"

# Set environment variables
set -gx PATH $PYTUI_PATH
set -gx VIRTUAL_ENV $PYTUI_VIRTUAL_ENV
set -gx VIRTUAL_ENV_PROMPT $PYTUI_VIRTUAL_ENV_PROMPT

if set -q PYTHONHOME
    set -e PYTHONHOME
end

if test -z "$VIRTUAL_ENV_DISABLE_PROMPT"
    # fish uses a function instead of an env var to generate the prompt.

    # Save the current fish_prompt function as the function _old_fish_prompt.
    functions -c fish_prompt _old_fish_prompt

    # With the original prompt function renamed, we can override with our own.
    function fish_prompt
        # Save the return status of the last command.
        set -l old_status $status

        # Output the venv prompt; color taken from the blue of the Python logo.
        printf "%s(%s)%s " (set_color 4B8BBE) $VIRTUAL_ENV_PROMPT (set_color normal)

        # Restore the return status of the previous command.
        echo "exit $old_status" | .
        # Output the original/"old" prompt.
        _old_fish_prompt
    end

end
