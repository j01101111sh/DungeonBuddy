# Devcontainer Aliases
alias dj='uv run python manage.py'
alias pcr='uv run pre-commit run'
alias ll='ls -al'
alias djr='dj runserver'
alias djt='uv run pytest'
alias djc='dj collectstatic --noinput'
alias djmm='dj makemigrations'
alias djm='dj migrate'
alias ds='./dev_setup.sh'
alias dsr='ds && djr'
alias prunelocal="git fetch --prune && git branch -vv | grep ': gone]' | awk '{print $1}' | xargs git branch -D"
alias gac='git add . && pcr'
