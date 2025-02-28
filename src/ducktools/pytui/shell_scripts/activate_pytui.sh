# This mostly exists in order to get the correct $PS1 value
source $HOME/.bashrc

# 'deactivate' in a pytui venv should just exit back to pytui
alias deactivate="exit"

# Replace the prompt unless it's specifically disabled
if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT-}" ] ; then
    export PS1="($PYTUI_VIRTUAL_ENV_PROMPT) $PS1"
fi

# bashrc running multiple times may have added dupes to PATH
# Use deduped PATH from pytui - which also includes the venv
export PATH=$PYTUI_PATH

# Hash to make sure path changes are added
hash -r 2>/dev/null
