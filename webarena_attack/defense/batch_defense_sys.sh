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
export OPENAI_BASE_URL="base-url"
export AGENTLAB_EXP_ROOT="results"
export AD_SERVER="localhost"
export PORT_SHIFT=2000
export AD_PATH="ad.json"
# for header style, use 03
# for popup style, use 01
# for side style use 08
export AD_ID="01"
export AD_STYLE="popup"
export AD_SCALE="1.0"
export AD_SERVER_PORT=$((61234 + $PORT_SHIFT))
export DEBUG_PORT=$((9222 + $PORT_SHIFT))

export EXTRA_TAG="defense_sys_l1_a11s_4o"
export SYSTEM_DEFENSE_LEVEL=1
python defense.py --model gpt-4o-2024-11-20 --type screenshot_a11y_tree

export EXTRA_TAG="defense_sys_l2_a11s_4o"
export SYSTEM_DEFENSE_LEVEL=2
python defense.py --model gpt-4o-2024-11-20 --type screenshot_a11y_tree

export EXTRA_TAG="defense_sys_l3_a11s_4o"
export SYSTEM_DEFENSE_LEVEL=3
python defense.py --model gpt-4o-2024-11-20 --type screenshot_a11y_tree
