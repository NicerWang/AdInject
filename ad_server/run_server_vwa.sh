#! /bin/bash

export PORT_SHIFT=2000
export AD_SERVER_PORT=$((61234 + $PORT_SHIFT))
python -u server.py > stdout_${PORT_SHIFT}.log 2> stderr_${PORT_SHIFT}.log