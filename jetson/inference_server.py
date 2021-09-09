"""
(c) Copyright 2021 Palantir Technologies Inc. All rights reserved.
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

import time
from grpc import ServicerContext, server, RpcContext

from proto import configuration_service_pb2 as api_conf
from proto import configuration_service_pb2_grpc as api_conf_grpc
from proto import processing_service_v2_pb2 as api_proc
from proto import processing_service_v2_pb2_grpc as api_proc_grpc

import utils
from model import InferenceModel

PORT = 50051
# change this path to your own TF 1.15 frozen inference graph
FROZEN_GRAPH_PATH = "/jetson_processor/ssd_mobilenet_v2_oid_v4_2018_12_12_frozen_graph.pb"


class InferenceConfiguration(api_conf_grpc.ConfigurationServiceServicer):
    def Configure(
        self, request: api_conf.ConfigurationRequest, context: RpcContext
    ) -> api_conf.ConfigurationResponse:
        print(
            "Received configuration request from {}:{}".format(
                request.orchestrator_name, request.orchestrator_version
            )
        )

        return api_conf.ConfigurationResponse(
            provider_name="inference-server",
            provider_version="0.1.0",
            version=api_conf.ProtocolVersion(
                v2=api_proc.ProcessorV2Config(
                    image_format=api_proc.PNG,
                    capabilities=[
                        api_proc.ProcessorV2Config.Capability.INFER
                    ],
                )
            ),
        )


def default_detection():
    return "generic detection"


class InferenceServer(api_proc_grpc.ProcessingServiceServicer):
    def __init__(self, thread_pool, inference_model):
        # specify your own dictionary of class ids to names here
        self.class_names = defaultdict(default_detection)
        self.class_names["391"] = "tree"
        self.thread_pool = thread_pool
        self.inference_model = inference_model

    def predict_on_image(self, image):
        return self.inference_model.run_inference(utils.read_png_or_tiff(image.path))

    def Infer(
        self, request: api_proc.InferenceRequest, context: ServicerContext
    ) -> api_proc.InferenceResponse:
        print(
            ("[GRPC] Frame #{} received. Stream_id: {}."
             "gRPC: {} tasks / {} threads").format(
                request.header.identifier.frame_id,
                request.header.identifier.stream_id,
                self.thread_pool._work_queue.qsize(),
                len(self.thread_pool._threads),
            )
        )

        start = time.time()
        inference_results = self.predict_on_image(
            request.frame.image.png_image)
        end = time.time()
        print("Done in seconds:" + str(end - start))
        return self.create_response(inference_results, request)

    def create_response(self, inference_results, request):
        list_of_inferences = []
        try:
            detection_boxes = inference_results["detection_boxes"][0]
            detection_classes = inference_results["detection_classes"][0]
            detection_scores = inference_results["detection_scores"][0]

            for i in range(len(detection_boxes)):
                x, y, x2, y2 = detection_boxes[i]
                upper_left = api_proc.UnitCoordinate(
                    row=x, col=y
                )
                lower_right = api_proc.UnitCoordinate(
                    row=x2, col=y2
                )

                if int(detection_classes[i]) == 1:
                    # End of interesting detections
                    break

                if str(int(detection_classes[i])) not in self.class_names:
                    print(f"Detected unknown object of class {int(detection_classes[i])}")
                    continue

                classifications = [
                    api_proc.Classification(
                        type=self.class_names[str(
                            int(detection_classes[i]))], confidence=detection_scores[i]
                    )
                ]
                box = api_proc.BoundingBox(
                    c0=upper_left, c1=lower_right, classifications=classifications
                )
                list_of_inferences.append(
                    api_proc.Inference(inferenceId=str(i), box=box))
        except Exception as e:
            print("Exception while creating inference list", e)
            pass

        print(f"Inference list: {list_of_inferences}")
        resp = api_proc.InferenceResponse(
            identifier=request.header.identifier,
            inferences=api_proc.Inferences(inference=list_of_inferences),
        )
        return resp


def main():
    thread_pool = ThreadPoolExecutor(max_workers=8)
    inference_model = InferenceModel(FROZEN_GRAPH_PATH)

    srv = server(thread_pool, maximum_concurrent_rpcs=8)
    api_conf_grpc.add_ConfigurationServiceServicer_to_server(
        InferenceConfiguration(), srv
    )
    try:
        api_proc_grpc.add_ProcessingServiceServicer_to_server(
            InferenceServer(thread_pool, inference_model), srv
        )
    except Exception as e:
        print("Error while initializing InferenceServer:")
        print(e)
        sys.exit(1)
    srv.add_insecure_port("[::]:{}".format(PORT))
    srv.start()
    print("AIP inference server listening on [::]:{}".format(PORT))
    srv.wait_for_termination()


if __name__ == "__main__":
    main()
