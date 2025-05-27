source /path/to/webarena-setup/visualwebarena/00_vars.sh

BASE_URL=http://$PUBLIC_HOSTNAME
# visualwebarena environment variables (change ports as needed)
export VWA_CLASSIFIEDS="$BASE_URL:$CLASSIFIEDS_PORT"
export VWA_CLASSIFIEDS_RESET_TOKEN="4b61655535e7ed388f0d40a93600254c"
export VWA_SHOPPING="$BASE_URL:$SHOPPING_PORT"
export VWA_REDDIT="$BASE_URL:$REDDIT_PORT"
export VWA_WIKIPEDIA="$BASE_URL:$WIKIPEDIA_PORT"
export VWA_HOMEPAGE="$BASE_URL:$HOMEPAGE_PORT"

# if your webarena instance offers the FULL_RESET feature (optional)
export VWA_FULL_RESET="$BASE_URL:$RESET_PORT"

export OPENAI_API_KEY="api-key"
export OPENAI_BASE_URL="api-base-url"

python -u speculate_user_query.py $VWA_CLASSIFIEDS classifieds >> speculate.log
python -u speculate_user_query.py $VWA_SHOPPING shopping >> speculate.log
python -u speculate_user_query.py $VWA_REDDIT reddit >> speculate.log
python -u speculate_user_query.py $VWA_WIKIPEDIA wikipedia >> speculate.log