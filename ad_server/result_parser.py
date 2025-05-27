import csv
import os

VWA_TASK_IDS = [
    6,
    7,
    12,
    13,
    15,
    16,
    19,
    21,
    23,
    27,
    28,
    30,
    31,
    34,
    41,
    42,
    43,
    50,
    56,
    58,
    83,
    94,
    97,
    105,
    106,
    124,
    125,
    129,
    160,
    174,
    205,
    209,
    269,
    270,
    271,
    275,
    303,
    304,
    306,
    310,
    311,
    324,
    325,
    376,
    377,
    380,
    384,
    444,
    457,
    460,
    463,
    473,
    482,
    493,
    497,
    498,
    500,
    501,
    504,
    505,
    506,
    520,
    521,
    525,
    637,
    638,
    656,
    660,
    666,
    670,
    717,
    872,
]
result_dir = "/path/to/your/result/directory"  # Replace with your actual directory path

for filename in os.listdir(result_dir):
    if filename.endswith(".log"):
        print("Processing file:", os.path.splitext(filename)[0])

        file_path = os.path.join(result_dir, filename)

        all = 0
        success = 0
        fail = 0
        success_steps = 0
        fail_task_ids = []

        with open(file_path, mode="r", encoding="utf-8") as file:
            csv_reader = csv.reader(file, delimiter=",")
            for row in csv_reader:
                current_task_id = VWA_TASK_IDS[all]
                all += 1
                if row[-2].strip() == "clicked":
                    success += 1
                    success_steps += int(row[-1])
                else:
                    fail += 1
                    fail_task_ids.append(current_task_id)

        print("all: ", all)
        print("success: ", success)
        print("fail: ", fail)
        print("total_steps: ", success_steps)
        if success > 0:
            print("avg_success_steps: ", success_steps / success)
        else:
            print("avg_success_steps: N/A")
        print("success_rate: ", success / all if all > 0 else 0)
        print("fail_task_ids: ", fail_task_ids)
        print("-" * 40)
