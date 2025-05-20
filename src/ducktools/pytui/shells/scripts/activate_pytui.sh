# Run the original bash config file *FIRST*
bashrcfile="$HOME/.bashrc"
[ -f "$bashrcfile" ] && source "$bashrcfile"

# 'deactivate' in a pytui venv should just exit back to pytui
alias deactivate="exit"

# Replace the prompt unless it's specifically disabled
if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT-}" ] ; then
    export PS1="($PYTUI_VIRTUAL_ENV_PROMPT) $PS1"
fi

# bashrc running multiple times may have added dupes to PATH
# Use deduped PATH from pytui - which also includes the venv
# Also export all of the environment variables without pytui prefix
export PATH=$PYTUI_PATH
export VIRTUAL_ENV=$PYTUI_VIRTUAL_ENV
export VIRTUAL_ENV_PROMPT=$PYTUI_VIRTUAL_ENV_PROMPT

unset PYTHONHOME

# Hash to make sure path changes are added
hash -r 2>/dev/null
