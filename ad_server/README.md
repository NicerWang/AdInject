# AD Server For AdInject

## Install

* Step1: `pip install -r requirements.txt`

* Step2(Optional): Remove `@retry` in `/path/to/python/site-packages/pycdp/asyncio.py#L398&L244`

# Usage

> After the server starts, view detailed documentation in `/docs`.

* For OSWorld, use `run_server_os.sh`

* For VisualWebArena, use `run_server_vwa.sh`

Ensure that `PORT_SHIFT` is the same in both `run_server_*.sh` and `bash_run.sh`, as this is the matching method for the ad server and envs.

Server will keep logs in `stdout_${PORT_SHIFT}.log` and `stderr_${PORT_SHIFT}.log`.

Attack result will be in `result_${PORT_SHIFT}.log`.