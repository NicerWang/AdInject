# AdInject For OSWorld

## Install

Step1. run `git clone https://github.com/xlang-ai/OSWorld`

Step2. run `cd OSWorld` then `pip install -e .` and `pip install requests`

Step3. ensure Docker is available, as our code is based on the Docker provider OSWorld

Step4. modify files follow [PORT_SHIFT FIX](#port_shift-fix)

Step5. fill API base url & keys

Step6. start file server for some tasks `.evaluation_examples/browser_file_server.sh`.


## Usage

* All the tasks we use are in `evaluation_examples`.

* For UI-TARS, use `batch_run_uitars.sh` (model deployment needed)

* For other models, use `batch_run.sh`

Ensure that `PORT_SHIFT` is the same in both `run_server_*.sh` and `bash_run.sh`, as this is the matching method for the ad server and envs.

## PORT_SHIFT FIX
replace desktop_env/providers/docker/provider.py#L71
```
    def _get_available_port_fixed(self, start_port: int) -> int:
        """Find the available port, retrying the same port until it becomes available."""
        while True:
            used_ports = self._get_used_ports()
            if start_port not in used_ports:
                return start_port
            time.sleep(2)
```

replace desktop_env/providers/docker/provider.py#L107
```
    port_shift = int(os.environ.get("PORT_SHIFT"))
    self.vnc_port = self._get_available_port_fixed(8006 + port_shift)
    self.server_port = self._get_available_port_fixed(5000 + port_shift)
    self.chromium_port = self._get_available_port_fixed(9222 + port_shift)
    self.vlc_port = self._get_available_port_fixed(8080 + port_shift)
```

replace desktop_env/providers/getters/chrome.py#L1180
```
    requests.post("http://" + host + ":" + str(server_port) + "/setup" + "/launch", headers=headers, data=payload)
```