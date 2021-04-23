# Introduction
AIP, or the AI Inference Platform, is Palantir Gotham’s platform to perform real-time augmentations and computations on streamed videos. AIP is the base platform that accepts video streams as input, and decodes them. Then, it runs the decoded video through zero or more “processor” services, which are responsible for actually processing the video. One common form of processing is to detect objects of a certain kind (using a pre-trained AI model) and augment the video with detections per frame. Another common form of processing is to identify the earth location where the video was taken, in precise latitudes and longitudes. AIP can handle any number of video streams simultaneously, also called “pipelines”. More recently, AIP also added support for processing raw folders of images in lieu of video streams.

The AIP dev team builds, improves and maintains the base AIP platform, and allows users of AIP to build their own processors with custom processing logic that suits their needs. In most cases, AIP and processors communicate with each other over a gRPC channel. A processor is a gRPC server listening on some port, and is registered with AIP via the AIP Config UI. A processor can be implemented in any language as long as it conforms to the processing and configuration Protocol Buffer definitions laid out by AIP.

# Getting Started
This SDK contains everything you need to get started building and testing an inference processor that runs images through a model for object detection, including a sample processor that runs out-of-the-box.

Refer to the [Introduction](https://palantir.github.io/aip-sdk/introduction) for an in-depth exploration of how to implement AIP processors for inference capabilities.
Refer to the [Quickstart](https://palantir.github.io/aip-sdk/quickstart) for simple steps to get the sample processor up and running in minutes.
