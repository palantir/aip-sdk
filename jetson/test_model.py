import time

import utils
from model import InferenceModel

FROZEN_GRAPH_PATH = "/jetson_4.3_processor/ssd_mobilenet_v2_oid_v4_2018_12_12_frozen_graph.pb"
IMAGE_PATH = "/jetson_4.3_processor/tree_test_image.png"

model = InferenceModel(FROZEN_GRAPH_PATH)
image = utils.read_png_or_tiff(IMAGE_PATH)

logs = []
for i in range(5):
    start = time.time()
    output = model.run_inference(image)
    end = time.time()
    logs.append("Inference %d completed in %s secs (%s ms)." %
                (i + 1, end - start, int((end - start) * 1000)))

print("Inference results:")
print(output)
print("=============================================================================")

for log in logs:
    print(log)

print("Note: If the first inference took a LOT of time, that's expected. Inferences 2 onwards are a better estimate of the speed.")
