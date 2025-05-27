#! /bin/bash
export OPENAI_API_KEY="uitars-api-key"
export OPENAI_BASE_URL="uitars-base-url"
export AD_SERVER="localhost"
export PORT_SHIFT=0
export AD_SERVER_PORT=$((61234 + $PORT_SHIFT))

# w/ attack
export AD_PATH="ad.json"
python run_uitars.py --headless --observation_type screenshot --test_all_meta_path evaluation_examples/test_both.json

# w/ attack[benign ad]
export AD_PATH="benign.json"
python run_uitars.py --headless --observation_type screenshot --test_all_meta_path evaluation_examples/test_both.json

# w/o attack[no ad]
export AD_ENABLE="raw"
python run_uitars.py --headless --observation_type screenshot --test_all_meta_path evaluation_examples/test_both.json