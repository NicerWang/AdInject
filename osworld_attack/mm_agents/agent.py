import base64
import json
import logging
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Dict, List

import backoff
import openai
import tiktoken
import anthropic
from PIL import Image
from requests.exceptions import SSLError

from mm_agents.accessibility_tree_wrap.heuristic_retrieve import (
    filter_nodes,
    draw_bounding_boxes,
)
from mm_agents.prompts import (
    SYS_PROMPT_IN_SCREENSHOT_OUT_CODE,
    SYS_PROMPT_IN_SCREENSHOT_OUT_ACTION,
    SYS_PROMPT_IN_A11Y_OUT_CODE,
    SYS_PROMPT_IN_A11Y_OUT_ACTION,
    SYS_PROMPT_IN_BOTH_OUT_CODE,
    SYS_PROMPT_IN_BOTH_OUT_ACTION,
    SYS_PROMPT_IN_SOM_OUT_TAG,
)

logger = logging.getLogger("desktopenv.agent")

pure_text_settings = ["a11y_tree"]

attributes_ns_ubuntu = "https://accessibility.windows.example.org/ns/attributes"
attributes_ns_windows = "https://accessibility.windows.example.org/ns/attributes"
state_ns_ubuntu = "https://accessibility.ubuntu.example.org/ns/state"
state_ns_windows = "https://accessibility.windows.example.org/ns/state"
component_ns_ubuntu = "https://accessibility.ubuntu.example.org/ns/component"
component_ns_windows = "https://accessibility.windows.example.org/ns/component"
value_ns_ubuntu = "https://accessibility.ubuntu.example.org/ns/value"
value_ns_windows = "https://accessibility.windows.example.org/ns/value"
class_ns_windows = "https://accessibility.windows.example.org/ns/class"
# More namespaces defined in OSWorld, please check desktop_env/server/main.py


# Function to encode the image
def encode_image(image_content):
    return base64.b64encode(image_content).decode("utf-8")


def encoded_img_to_pil_img(data_str):
    base64_str = data_str.replace("data:image/png;base64,", "")
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))

    return image


def save_to_tmp_img_file(data_str):
    base64_str = data_str.replace("data:image/png;base64,", "")
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))

    tmp_img_path = os.path.join(tempfile.mkdtemp(), "tmp_img.png")
    image.save(tmp_img_path)

    return tmp_img_path


def linearize_accessibility_tree(accessibility_tree, platform="ubuntu"):

    if platform == "ubuntu":
        _attributes_ns = attributes_ns_ubuntu
        _state_ns = state_ns_ubuntu
        _component_ns = component_ns_ubuntu
        _value_ns = value_ns_ubuntu
    elif platform == "windows":
        _attributes_ns = attributes_ns_windows
        _state_ns = state_ns_windows
        _component_ns = component_ns_windows
        _value_ns = value_ns_windows
    else:
        raise ValueError("Invalid platform, must be 'ubuntu' or 'windows'")

    filtered_nodes = filter_nodes(ET.fromstring(accessibility_tree), platform)
    # linearized_accessibility_tree = [
    #     "tag\tname\ttext\tclass\tdescription\tposition (top-left x&y)\tsize (w&h)"
    # ]
    linearized_accessibility_tree = [
        "tag\tname\ttext\tclass\tdescription\tposition (center x&y)\tsize (w&h)"
    ]

    # Linearize the accessibility tree nodes into a table format
    for node in filtered_nodes:
        if node.text:
            text = (
                node.text
                if '"' not in node.text
                else '"{:}"'.format(node.text.replace('"', '""'))
            )

        elif node.get("{{{:}}}class".format(class_ns_windows), "").endswith(
            "EditWrapper"
        ) and node.get("{{{:}}}value".format(_value_ns)):
            node_text = node.get("{{{:}}}value".format(_value_ns), "")
            text = (
                node_text
                if '"' not in node_text
                else '"{:}"'.format(node_text.replace('"', '""'))
            )
        else:
            text = '""'

        top_left = eval(node.get("{{{:}}}screencoord".format(_component_ns), ""))
        size = eval(node.get("{{{:}}}size".format(_component_ns), ""))
        center_coord = (
            int(top_left[0]) + int(size[0]) // 2,
            int(top_left[1]) + int(size[1]) // 2,
        )

        linearized_accessibility_tree.append(
            "{:}\t{:}\t{:}\t{:}\t{:}\t{:}\t{:}".format(
                node.tag,
                node.get("name", ""),
                text,
                (
                    node.get("{{{:}}}class".format(_attributes_ns), "")
                    if platform == "ubuntu"
                    else node.get("{{{:}}}class".format(class_ns_windows), "")
                ),
                node.get("{{{:}}}description".format(_attributes_ns), ""),
                center_coord,
                node.get("{{{:}}}size".format(_component_ns), ""),
            )
        )

    return "\n".join(linearized_accessibility_tree)


def tag_screenshot(screenshot, accessibility_tree, platform="ubuntu"):
    nodes = filter_nodes(
        ET.fromstring(accessibility_tree), platform=platform, check_image=True
    )
    # Make tag screenshot
    marks, drew_nodes, element_list, tagged_screenshot = draw_bounding_boxes(
        nodes, screenshot
    )

    return marks, drew_nodes, tagged_screenshot, element_list


def parse_actions_from_string(input_string):
    if input_string.strip() in ["WAIT", "DONE", "FAIL"]:
        return [input_string.strip()]
    # Search for a JSON string within the input string
    actions = []
    matches = re.findall(r"```json\s+(.*?)\s+```", input_string, re.DOTALL)
    if matches:
        # Assuming there's only one match, parse the JSON string into a dictionary
        try:
            for match in matches:
                action_dict = json.loads(match)
                actions.append(action_dict)
            return actions
        except json.JSONDecodeError as e:
            return f"Failed to parse JSON: {e}"
    else:
        matches = re.findall(r"```\s+(.*?)\s+```", input_string, re.DOTALL)
        if matches:
            # Assuming there's only one match, parse the JSON string into a dictionary
            try:
                for match in matches:
                    action_dict = json.loads(match)
                    actions.append(action_dict)
                return actions
            except json.JSONDecodeError as e:
                return f"Failed to parse JSON: {e}"
        else:
            try:
                action_dict = json.loads(input_string)
                return [action_dict]
            except json.JSONDecodeError:
                raise ValueError("Invalid response format: " + input_string)


def parse_code_from_string(input_string):
    input_string = "\n".join(
        [line.strip() for line in input_string.split(";") if line.strip()]
    )
    if input_string.strip() in ["WAIT", "DONE", "FAIL"]:
        return [input_string.strip()]

    # This regular expression will match both ```code``` and ```python code```
    # and capture the `code` part. It uses a non-greedy match for the content inside.
    pattern = r"```(?:\w+\s+)?(.*?)```"
    # Find all non-overlapping matches in the string
    matches = re.findall(pattern, input_string, re.DOTALL)

    # The regex above captures the content inside the triple backticks.
    # The `re.DOTALL` flag allows the dot `.` to match newline characters as well,
    # so the code inside backticks can span multiple lines.

    # matches now contains all the captured code snippets

    codes = []

    for match in matches:
        match = match.strip()
        commands = [
            "WAIT",
            "DONE",
            "FAIL",
        ]  # fixme: updates this part when we have more commands

        if match in commands:
            codes.append(match.strip())
        elif match.split("\n")[-1] in commands:
            if len(match.split("\n")) > 1:
                codes.append("\n".join(match.split("\n")[:-1]))
            codes.append(match.split("\n")[-1])
        else:
            codes.append(match)

    return codes


def parse_code_from_som_string(input_string, masks):
    # parse the output string by masks
    tag_vars = ""
    for i, mask in enumerate(masks):
        x, y, w, h = mask
        tag_vars += (
            "tag_"
            + str(i + 1)
            + "="
            + "({}, {})".format(int(x + w // 2), int(y + h // 2))
        )
        tag_vars += "\n"

    actions = parse_code_from_string(input_string)

    for i, action in enumerate(actions):
        if action.strip() in ["WAIT", "DONE", "FAIL"]:
            pass
        else:
            action = tag_vars + action
            actions[i] = action

    return actions


def trim_accessibility_tree(linearized_accessibility_tree, max_tokens):
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(linearized_accessibility_tree)
    if len(tokens) > max_tokens:
        linearized_accessibility_tree = enc.decode(tokens[:max_tokens])
        linearized_accessibility_tree += "[...]\n"
    return linearized_accessibility_tree


class PromptAgent:
    def __init__(
        self,
        platform="ubuntu",
        model="gpt-4-vision-preview",
        max_tokens=1500,
        top_p=0.9,
        temperature=0.5,
        action_space="computer_13",
        observation_type="screenshot_a11y_tree",
        # observation_type can be in ["screenshot", "a11y_tree", "screenshot_a11y_tree", "som"]
        max_trajectory_length=3,
        a11y_tree_max_tokens=10000,
    ):
        self.platform = platform
        self.model = model
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.action_space = action_space
        self.observation_type = observation_type
        self.max_trajectory_length = max_trajectory_length
        self.a11y_tree_max_tokens = a11y_tree_max_tokens

        self.thoughts = []
        self.actions = []
        self.observations = []

        if observation_type == "screenshot":
            if action_space == "computer_13":
                self.system_message = SYS_PROMPT_IN_SCREENSHOT_OUT_ACTION
            elif action_space == "pyautogui":
                self.system_message = SYS_PROMPT_IN_SCREENSHOT_OUT_CODE
            else:
                raise ValueError("Invalid action space: " + action_space)
        elif observation_type == "a11y_tree":
            if action_space == "computer_13":
                self.system_message = SYS_PROMPT_IN_A11Y_OUT_ACTION
            elif action_space == "pyautogui":
                self.system_message = SYS_PROMPT_IN_A11Y_OUT_CODE
            else:
                raise ValueError("Invalid action space: " + action_space)
        elif observation_type == "screenshot_a11y_tree":
            if action_space == "computer_13":
                self.system_message = SYS_PROMPT_IN_BOTH_OUT_ACTION
            elif action_space == "pyautogui":
                self.system_message = SYS_PROMPT_IN_BOTH_OUT_CODE
            else:
                raise ValueError("Invalid action space: " + action_space)
        elif observation_type == "som":
            if action_space == "computer_13":
                raise ValueError("Invalid action space: " + action_space)
            elif action_space == "pyautogui":
                self.system_message = SYS_PROMPT_IN_SOM_OUT_TAG
            else:
                raise ValueError("Invalid action space: " + action_space)
        else:
            raise ValueError("Invalid experiment type: " + observation_type)

    def predict(self, instruction: str, obs: Dict) -> List:
        """
        Predict the next action(s) based on the current observation.
        """
        system_message = (
            self.system_message
            + "\nYou are asked to complete the following task: {}".format(instruction)
        )

        # Prepare the payload for the API call
        messages = []
        masks = None

        messages.append(
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_message},
                ],
            }
        )

        # Append trajectory
        assert len(self.observations) == len(self.actions) and len(self.actions) == len(
            self.thoughts
        ), "The number of observations and actions should be the same."

        if len(self.observations) > self.max_trajectory_length:
            if self.max_trajectory_length == 0:
                _observations = []
                _actions = []
                _thoughts = []
            else:
                _observations = self.observations[-self.max_trajectory_length :]
                _actions = self.actions[-self.max_trajectory_length :]
                _thoughts = self.thoughts[-self.max_trajectory_length :]
        else:
            _observations = self.observations
            _actions = self.actions
            _thoughts = self.thoughts

        for previous_obs, previous_action, previous_thought in zip(
            _observations, _actions, _thoughts
        ):

            # {{{1
            if self.observation_type == "screenshot_a11y_tree":
                _screenshot = previous_obs["screenshot"]
                _linearized_accessibility_tree = previous_obs["accessibility_tree"]

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Given the screenshot and info from accessibility tree as below:\n{}\nWhat's the next step that you will do to help with the task?".format(
                                    _linearized_accessibility_tree
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{_screenshot}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                )
            elif self.observation_type in ["som"]:
                _screenshot = previous_obs["screenshot"]

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Given the tagged screenshot as below. What's the next step that you will do to help with the task?",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{_screenshot}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                )
            elif self.observation_type == "screenshot":
                _screenshot = previous_obs["screenshot"]

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Given the screenshot as below. What's the next step that you will do to help with the task?",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{_screenshot}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                )
            elif self.observation_type == "a11y_tree":
                _linearized_accessibility_tree = previous_obs["accessibility_tree"]

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Given the info from accessibility tree as below:\n{}\nWhat's the next step that you will do to help with the task?".format(
                                    _linearized_accessibility_tree
                                ),
                            }
                        ],
                    }
                )
            else:
                raise ValueError(
                    "Invalid observation_type type: " + self.observation_type
                )  # 1}}}

            messages.append(
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                previous_thought.strip()
                                if len(previous_thought) > 0
                                else "No valid action"
                            ),
                        },
                    ],
                }
            )

        # {{{1
        if self.observation_type in ["screenshot", "screenshot_a11y_tree"]:
            base64_image = encode_image(obs["screenshot"])
            linearized_accessibility_tree = (
                linearize_accessibility_tree(
                    accessibility_tree=obs["accessibility_tree"], platform=self.platform
                )
                if self.observation_type == "screenshot_a11y_tree"
                else None
            )
            logger.debug("LINEAR AT: %s", linearized_accessibility_tree)

            if linearized_accessibility_tree:
                linearized_accessibility_tree = trim_accessibility_tree(
                    linearized_accessibility_tree, self.a11y_tree_max_tokens
                )

            if self.observation_type == "screenshot_a11y_tree":
                self.observations.append(
                    {
                        "screenshot": base64_image,
                        "accessibility_tree": linearized_accessibility_tree,
                    }
                )
            else:
                self.observations.append(
                    {"screenshot": base64_image, "accessibility_tree": None}
                )

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Given the screenshot as below. What's the next step that you will do to help with the task?"
                                if self.observation_type == "screenshot"
                                else "Given the screenshot and info from accessibility tree as below:\n{}\nWhat's the next step that you will do to help with the task?".format(
                                    linearized_accessibility_tree
                                )
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            )
        elif self.observation_type == "a11y_tree":
            linearized_accessibility_tree = linearize_accessibility_tree(
                accessibility_tree=obs["accessibility_tree"], platform=self.platform
            )
            logger.debug("LINEAR AT: %s", linearized_accessibility_tree)

            if linearized_accessibility_tree:
                linearized_accessibility_tree = trim_accessibility_tree(
                    linearized_accessibility_tree, self.a11y_tree_max_tokens
                )

            self.observations.append(
                {
                    "screenshot": None,
                    "accessibility_tree": linearized_accessibility_tree,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Given the info from accessibility tree as below:\n{}\nWhat's the next step that you will do to help with the task?".format(
                                linearized_accessibility_tree
                            ),
                        }
                    ],
                }
            )
        elif self.observation_type == "som":
            # Add som to the screenshot
            masks, drew_nodes, tagged_screenshot, linearized_accessibility_tree = (
                tag_screenshot(
                    obs["screenshot"], obs["accessibility_tree"], self.platform
                )
            )
            base64_image = encode_image(tagged_screenshot)
            logger.debug("LINEAR AT: %s", linearized_accessibility_tree)

            if linearized_accessibility_tree:
                linearized_accessibility_tree = trim_accessibility_tree(
                    linearized_accessibility_tree, self.a11y_tree_max_tokens
                )

            self.observations.append(
                {
                    "screenshot": base64_image,
                    "accessibility_tree": linearized_accessibility_tree,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Given the tagged screenshot and info from accessibility tree as below:\n{}\nWhat's the next step that you will do to help with the task?".format(
                                linearized_accessibility_tree
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            )
        else:
            raise ValueError(
                "Invalid observation_type type: " + self.observation_type
            )  # 1}}}

        # with open("messages.json", "w") as f:
        #     f.write(json.dumps(messages, indent=4))

        # logger.info("PROMPT: %s", messages)

        try:
            response = self.call_llm(
                {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                }
            )
        except Exception as e:
            logger.error("Failed to call" + self.model + ", Error: " + str(e))
            response = ""

        logger.info("RESPONSE: %s", response)

        try:
            actions = self.parse_actions(response, masks)
            self.thoughts.append(response)
        except ValueError as e:
            print("Failed to parse action from response", e)
            actions = None
            self.thoughts.append("")

        return response, actions

    @backoff.on_exception(
        backoff.constant,
        # here you should add more model exceptions as you want,
        # but you are forbidden to add "Exception", that is, a common type of exception
        # because we want to catch this kind of Exception in the outside to ensure each example won't exceed the time limit
        (
            # General exceptions
            SSLError,
            # OpenAI exceptions
            openai.RateLimitError,
            openai.BadRequestError,
            openai.InternalServerError,
            # Google exceptions
            # InvalidArgument,
            # ResourceExhausted,
            # InternalServerError,
            # BadRequest,
            # Groq exceptions
            # todo: check
        ),
        interval=30,
        max_tries=10,
    )
    def call_llm(self, payload):
        if "claude" in payload["model"]:
            for message in payload["messages"]:
                if message["role"] == "system":
                    message["role"] = "user"
            # Call OpenAI API
        client = openai.OpenAI()
        completion = client.chat.completions.create(
            model=payload["model"],
            messages=payload["messages"],
            n=1,
            temperature=payload["temperature"],
            max_tokens=payload["max_tokens"],
            top_p=payload["top_p"],
        )
        return completion.choices[0].message.content

    def parse_actions(self, response: str, masks=None):

        if self.observation_type in ["screenshot", "a11y_tree", "screenshot_a11y_tree"]:
            # parse from the response
            if self.action_space == "computer_13":
                actions = parse_actions_from_string(response)
            elif self.action_space == "pyautogui":
                actions = parse_code_from_string(response)
            else:
                raise ValueError("Invalid action space: " + self.action_space)

            self.actions.append(actions)

            return actions
        elif self.observation_type in ["som"]:
            # parse from the response
            if self.action_space == "computer_13":
                raise ValueError("Invalid action space: " + self.action_space)
            elif self.action_space == "pyautogui":
                actions = parse_code_from_som_string(response, masks)
            else:
                raise ValueError("Invalid action space: " + self.action_space)

            self.actions.append(actions)

            return actions

    def reset(self, _logger=None):
        global logger
        logger = (
            _logger if _logger is not None else logging.getLogger("desktopenv.agent")
        )

        self.thoughts = []
        self.actions = []
        self.observations = []
