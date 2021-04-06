# Introduction
AIP, or the AI Inference Platform, is Palantir Gotham's proprietary platform to perform real-time augmentations and computations on streamed videos. AIP is the base platform that accepts video streams as input, and decodes them. Then, it runs the decoded video through zero or more "processor" services, which are responsible for actually processing the video. One common form of processing is to detect objects of a certain kind (using a pre-trained AI model) and augment the video with detections per frame. Another common form of processing is to identify the earth location where the video was taken, in precise latitudes and longitudes. AIP can handle any number of video streams simultaneously, also called "pipelines". More recently, AIP also added support for processing raw folders of images in lieu of video streams.

The AIP dev team builds, improves and maintains the base AIP platform, and allows users of AIP to build their own processors with custom processing logic that suits their needs. In most cases, AIP and processors communicate with each other over a gRPC channel. A processor is a gRPC server listening on some port, and is registered with AIP via the AIP Config UI. A processor can be implemented in any language as long as it conforms to the processing and configuration Protocol Buffer definitions laid out by AIP.

The general way to use AIP is:
1) Register one or more processor(s) of interest.
2) Create a new pipeline with a video source and sink location. By default, it is disabled.
3) Add the processor(s) to the pipeline.
4) Enable the pipeline, then AIP starts feeding video frames through the pipeline.

Processors can be added to and removed from an enabled (live) pipeline, with AIP handling all the frame routing logic behind the scenes.

# Implementing a Python inference processor
The AIP SDK contains a fully-functional processor that uses PyTorch to perform plane detection. You can build the Docker image and run it out-of-the-box. Refer to the [Quickstart](https://pages.github.palantir.build/video/aip-sdk/quickstart) for simple steps to get the sample processor up and running.

Read on to better understand different parts of the implementation.

## Pull proto files
The latest proto files are [available for download here](https://bintray.com/palantir/releases/download_file?file_path=com%2Fpalantir%2Faip%2Fprocessors%2Fapi%2Faip-processor-api%2F0.0.1%2Faip-processor-api-0.0.1.jar). Download them, un-jar the file, and copy the `configuration-service.proto` and `processing-service-v2.proto` files into a `proto` folder, **created in the root folder**. That's it! When you build the docker image, the proto files will automatically be compiled.

## Implement Infer method
Implement Infer method in `inference_server.py`. This is the primary handler that should encapsulate inference logic. For example, it may make an external API call to a running model, or may invoke a locally running model. The argument is an `InferenceRequest`, which contains the image to run the model on and additional metadata if available. The expected return type is an `InferenceResponse` which contains results of model prediction on the image. Please refer to the proto file for the structures of these data types. They are pasted below for your easy reference, but note that the proto file is the ultimate source of truth for the latest structure.

You can use OpenCV to read in the image bytes from the `InferenceRequest` object. If it is RGB, it will be at the following path: `request.frame.image.rgb_image.path`. If it is BGR, it will be at the following path: `request.frame.image.bgr_image.path`. The choice of RGB, or BGR (or PNG or TIFF) is in your hands. When you implement the `Configure` method (see the next section of the docs), you need to specify what kind of image format AIP should send your processor. Note that with PNG or TIFF, there is an extra encoding overhead incurred, so be sure you really need images in those formats before choosing them. For example, if you have to make an API call to a model and it expects a PNG, then you may choose PNG. If you do have flexibility in image formats, it is faster and highly recommended to choose RGB or BGR instead.

The following is an example of how you would implement the `Infer` method that receives an RGB image and runs it through a local CPU-based model, sending back the response. Please refer to `inference_server.py` for the full implementation.
```python
def Infer(
    self, request: api_proc.InferenceRequest, context: ServicerContext
) -> api_proc.InferenceResponse:
        print("Received Infer request from AIP...")
        inference_results = self.predict_on_image(request.frame.image.rgb_image.path)
        print("Sending InferenceResponse.")
        # packages up the detections into the `InferenceResponse` proto structure
        return self.create_response(inference_results, request)
```

As a sneak preview, these are the key proto messages required here (please see full proto file for all definitions):
```
message InferenceRequest {
    RequestHeader header = 1;
    Frame frame = 2;
}

message Frame {
    Image image = 1;
    UasMetadata uas_metadata = 2;
}

message InferenceResponse {
    Identifier identifier = 1;
    Inferences inferences = 2;
}

message Inferences {
    repeated Inference inference = 1;
}

message Inference {
    /** Persistent id of a particular inference that's used to tie together inferences across frames. */
    string inferenceId = 1;

    oneof inference {
        BoundingBox box = 2;
        BoundingPolygon polygon = 3;
        GeoBoundingBox geo_box = 5;
        GeoBoundingPolygon geo_polygon = 6;
    }

    Velocity velocity = 4;

    /** Value in the range [0,1] representing how likely the inference corresponds to the same object across frames. */
    double track_confidence = 7;
}
```

## Advertise the INFER capability and expected image format
AIP processors are designed to be very versatile in functionality. They may be built to perform numerous augmentations or modifications to an incoming video frame. Currently, AIP primarily supports the following capabilities, in this order of importance:
* Inference
    * Example: Running a model on the video frame or it's metadata, for classification, object detection, semantic segmentation and so on.
* Geo-registration
    * Example: Figuring out the earth location captured by the frame, in precise latitudes and longitudes (of the 4 corners and points in between)
    * Example: Applying math-based smoothing logic to stabilize an imprecise, shaky earth location

AIP also supports numerous image formats, including RGB, BGR, PNG and TIFF. The first two are raw, while the last two are encoded. As explained in the previous section, please choose your image format carefully depending on your needs, asking yourself if you really need the extra compression (and hence higher latency) offered by PNG and TIFF.

Once you have determined what your processor's capability and image format should be, you need to register your processor with AIP and let it know that it is ready to receive requests of the specified capability, with the specified image format.

Here is how configuration happens, for an Inference processor requiring a RGB image:

1) You implement the `Configure` method, like the following. Fill out the 4 required fields: `provider_name`, `provider_version`, `image_format` and `capabilities`.
```python
    def Configure(self,
                  request: api_conf.ConfigurationRequest,
                  context: grpc.RpcContext) -> api_conf.ConfigurationResponse:
        print("Received configuration request from {}:{}".format(
            request.orchestrator_name,
            request.orchestrator_version))

        return api_conf.ConfigurationResponse(
            <b>provider_name="inference-server"</b>, # specify the name of your processor (you can make one up)
            <b>provider_version="0.1.0"</b>, # specify the version of your processor (as per your own versioning schema)
            version=api_conf.ProtocolVersion(
                v2=api_proc.ProcessorV2Config(
                    <b>image_format=api_proc.RGB888</b>, # you could also specify BGR888 if you prefer BGR images instead
                    capabilities=[
                        <b>api_proc.ProcessorV2Config.Capability.INFER</b>], # specify INFER capability here (refer to proto file for list of supported capabilities)
                )
            )
        )
```
2) You run your processor on some port. This starts a gRPC server listening to a port.
3) You add the processor to the AIP Config UI (on the left sidebar), including which port the processor is listening on. This way, AIP knows about the processor for the first time. (See next section for detailed guide and video walkthrough)
4) When the processor is added, AIP sends a `ConfigurationRequest` to the processor at that port.
5) Your processor handles the request using the `Configure` handler defined above and sends back a `ConfigurationResponse`.
6) AIP receives the response, and registers the processor along with its preferences. It is ready to start sending images in the expected format to the processor.

Steps 1, 2, and 3 are what you have to do manually, while Steps 4 and 6 are what AIP does for you. Step 5 is merely where your implementation of the `Configure` method runs.

## Adding a processor in the AIP Config UI

### Video Walkthrough
[Watch this walkthrough video](https://palantir.box.com/s/g58r83a5ney9uvhlyfx763pepbt7r6lb) to create your first processor and add it to a pipeline via the AIP Config App. For most use cases, the video provides the simplest way to get your processor up and running quickly.

### Verify working pipeline
To verify that your pipeline is working, you should seek to confirm that your processor is receiving frames, performing inference successfully, and returning correct detections back. An easy way to check this is by clicking on the Youtube-look-alike "Play" button (3rd from the right) on the top right of the pipeline panel. With some delay, it will open up a center modal with a preview video, including overlaid AI detections in the form of dots (instead of bounding boxes, as those are heavier to render). Rest assured, the underlying saved detections are full bounding boxes.

### Multiple processor copies
You may want to run multiple copies of your processor when a single instance will not be able to handle more than a single video feed at a time. To do so, enter Advanced Options on the left sidebar, click on the pencil icon (edit) on your processor, and then press the `+ Add Instance` button to enter details for a new instance running on a **different port**. Adding N instances allows you to attach this processor to N different pipelines at the same time.

### Chaining processors
AIP is designed to enable a chain of processors, with the output of one becoming the input of another. This allows you to accomplish complex functionality such as first performing inference to obtain bounding boxes, followed by applying a correction logic to fix any incorrect detections, and finally writing to a video file or udp sink.

Say you have a pipeline Input --> Processor A --> Output. You now wish to add a processor B that takes A's output as input. Simply click on A's node in the graph visualization. In the modal that comes up on the right side, choose "Add after", specify processor B, and click "Add". You should see the graph visualization being updated to Input --> Processor A --> Processor B --> Output.

### Parallel processors
AIP is designed to enable multiple processors running in parallel on a single video feed. For example, you may want to perform inference and geo-registration simultaneously, since they are independent of each other. Simply add both processors to the pipeline via the `+ Add processor` button shown in the video. You should see the graph visualization reflect this:

```
Input ---> Processor A ----> Output
      \                   /
       --> Processor B -->
```

### Advanced use cases
Most use cases should be covered by the above functionality. If you have a unique use case, please reach out to the AIP dev team for guidance.
