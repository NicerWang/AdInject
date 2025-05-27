#! /bin/bash

export OPENAI_API_KEY="api-key"
export OPENAI_BASE_URL="base-url"
export AD_SERVER="localhost"
export PORT_SHIFT=0
export AD_SERVER_PORT=$((61234 + $PORT_SHIFT))

# w/ attack
export AD_PATH="ad.json"
python run.py --headless --observation_type screenshot --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

python run.py --headless --observation_type screenshot_a11y_tree --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot_a11y_tree --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot_a11y_tree --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

python run.py --headless --observation_type som --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type som --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type som --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

# w/ attack[benign ad]
export AD_PATH="benign.json"
python run.py --headless --observation_type screenshot --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

python run.py --headless --observation_type screenshot_a11y_tree --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot_a11y_tree --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot_a11y_tree --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

python run.py --headless --observation_type som --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type som --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type som --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json


# w/o attack[no ad]
export AD_ENABLE="false"
python run.py --headless --observation_type screenshot --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

python run.py --headless --observation_type screenshot_a11y_tree --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot_a11y_tree --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type screenshot_a11y_tree --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json

python run.py --headless --observation_type som --model claude-3-5-sonnet-20241022 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type som --model claude-3-7-sonnet-20250219 --test_all_meta_path evaluation_examples/test_both.json
python run.py --headless --observation_type som --model gpt-4o-2024-11-20 --test_all_meta_path evaluation_examples/test_both.json
