set -eo pipefail

COLOR_GREEN=$(tput setaf 2)
COLOR_BLUE=$(tput setaf 4)
COLOR_NC=$(tput sgr0) # No Color

export DJANGO_SETTINGS_MODULE="config.settings.local"

cd "$(dirname "$0")/../.."

echo "${COLOR_BLUE}Starting mypy${COLOR_NC}"
python -m dmypy run -- .
echo "OK"

echo "${COLOR_BLUE}Starting Django Test with coverage${COLOR_NC}"
python -m coverage run manage.py test
python -m coverage report -m
python -m coverage html

echo "${COLOR_GREEN}Successfully Run Mypy and Test!!${COLOR_NC}"
