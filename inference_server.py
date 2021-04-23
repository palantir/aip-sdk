"""
(c) Copyright 2021 Palantir Technologies Inc. All rights reserved.
"""

from concurrent.futures import ThreadPoolExecutor
import sys

import cv2
import numpy as np
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from grpc import ServicerContext, server, RpcContext

from proto import configuration_service_pb2 as api_conf
from proto import configuration_service_pb2_grpc as api_conf_grpc
from proto import processing_service_v2_pb2 as api_proc
from proto import processing_service_v2_pb2_grpc as api_proc_grpc

PORT = 50051  # TODO: specify port that the gRPC server should listen on


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
            # TODO: replace with your own processor name
            provider_name="inference-server",
            # TODO: replace with your own processor version (as per your own
            # versioning schema)
            provider_version="0.1.0",
            version=api_conf.ProtocolVersion(
                v2=api_proc.ProcessorV2Config(
                    # TODO: replace with your expected image format
                    image_format=api_proc.BGR888,
                    # TODO: replace with your processor's capabilities
                    capabilities=[
                        api_proc.ProcessorV2Config.Capability.INFER
                    ],
                )
            ),
        )


class InferenceServer(api_proc_grpc.ProcessingServiceServicer):
    def __init__(self, thread_pool):
        self.model_cfg = self._configure_model()
        self.class_names = [
            "Small Civil Transport/Utility",
            "Medium Civil Transport/Utility",
            "Large Civil Transport/Utility",
        ]
        self.thread_pool = thread_pool

        # This is where Detectron2's model is loaded.
        # The `DefaultPredictor` expects a BGR image for inference, so we have
        # specified the image format as `BGR888` during the configuration
        # step, and also read the `bgr_image.path` field from the
        # `InferenceRequest`.
        self.predictor = DefaultPredictor(self.model_cfg)

    def _configure_model(self):
        cfg = get_cfg()
        cfg.merge_from_file("./model/faster_rcnn_R_101_FPN_3x.yaml")
        cfg.MODEL.WEIGHTS = "./model/model_final_f6e8b1.pkl"

        cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = (
            256  # faster, and good enough for this toy dataset (default: 512)
        )
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 3
        # set a custom testing threshold
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.1

        # TODO: Specify device to run model on.
        # TODO: Also set CUDA_VISIBLE_DEVICES when running the processor.
        cfg.MODEL.DEVICE = "cpu"  # run inference on the CPU
        # cfg.MODEL.DEVICE='cuda:1' # use this instead to run it on GPU 1.

        return cfg

    def _read_png_or_tiff(self, image):
        return cv2.imread(image.path)

    def _read_bgr888_or_rgb888(self, image):
        with open(image.path, "rb") as infile:
            data = infile.read()
            arr = np.frombuffer(data, dtype=np.uint8)
            return arr.reshape(image.height, image.width, 3)

    def predict_on_image(self, image):
        print("Reading image at: " + image.path)
        im = self._read_bgr888_or_rgb888(image)
        print("Predicting on image...")
        return self.predictor(im)

    def Infer(
        self, request: api_proc.InferenceRequest, context: ServicerContext
    ) -> api_proc.InferenceResponse:
        # TODO: implement this method to invoke your model

        print(
            ("[GRPC] Frame #{} received. Stream_id: {}."
             "gRPC: {} tasks / {} threads").format(
                request.header.identifier.frame_id,
                request.header.identifier.stream_id,
                self.thread_pool._work_queue.qsize(),
                len(self.thread_pool._threads),
            )
        )

        inference_results = self.predict_on_image(
            request.frame.image.bgr_image)
        print("Sending InferenceResponse.")
        print("----------------------------")
        return self.create_response(inference_results, request)

    def create_response(self, inference_results, request):
        # TODO: modify this method to construct InferenceResponse based on your
        # inference results
        list_of_inferences = []
        inference_instances = inference_results["instances"]

        bounding_boxes = inference_instances._fields["pred_boxes"].tensor.cpu()
        scores = inference_instances._fields["scores"].cpu()
        classes = inference_instances._fields["pred_classes"].cpu()

        image_width = float(request.frame.image.bgr_image.width)
        image_height = float(request.frame.image.bgr_image.height)

        for i in range(len(bounding_boxes)):
            x, y, x2, y2 = bounding_boxes[i]
            upper_left = api_proc.UnitCoordinate(
                row=x / image_width, col=y / image_height
            )
            lower_right = api_proc.UnitCoordinate(
                row=x2 / image_width, col=y2 / image_height
            )
            classifications = [
                api_proc.Classification(
                    type=self.class_names[classes[i]], confidence=scores[i]
                )
            ]
            box = api_proc.BoundingBox(
                c0=upper_left, c1=lower_right, classifications=classifications
            )
            list_of_inferences.append(
                api_proc.Inference(inferenceId=str(i), box=box))

        return api_proc.InferenceResponse(
            identifier=request.header.identifier,
            inferences=api_proc.Inferences(inference=list_of_inferences),
        )


def main():
    # TODO: specify how many gRPC server threads should handle incoming
    # requests. If all threads are being used, newer requests are
    # automatically queued, as long as we're not at the limit of
    # maximum_concurrent_rpcs (see below)
    thread_pool = ThreadPoolExecutor(max_workers=8)

    # TODO: specify how many requests can be concurrently processed
    # if another request comes in during that time, it is automatically
    # rejected by gRPC
    srv = server(thread_pool, maximum_concurrent_rpcs=8)
    api_conf_grpc.add_ConfigurationServiceServicer_to_server(
        InferenceConfiguration(), srv
    )
    try:
        api_proc_grpc.add_ProcessingServiceServicer_to_server(
            InferenceServer(thread_pool), srv
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
