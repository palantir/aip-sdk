# Quickstart

Jump to the [Introduction](https://palantir.github.io/aip-sdk/introduction) for a brief introduction to the AIP SDK.

The AIP SDK contains three fully-functional processors. 
One uses PyTorch to perform plane detection and runs on an x86 64 bit machine. 
The other two use a model trained on the OpenImages v4 dataset (so it can detect a lot of common things) 
and runs on an NVIDIA Jetson AGX Xavier. Of these last two processors that use the OpenImages model, one is configured to run with JetPack 4.3,
whereas the second is configured to run with JetPack 4.6
You can build these Docker images and run them out-of-the-box.


## x86 64 bit processor

### 1) Clone the AIP SDK source code from the [Github repository](https://github.com/palantir/aip-sdk)

### 2) Build the processor
```bash
./build_image.sh -f Dockerfile.x86_64 -t myx86processor:1.0.0
```

### 3) Run the processor on port 50051 (default)
```bash
./start_x86_64_container.sh -t myx86processor:1.0.0
```

#### Expected prints after successful initialization

1) It will download a PyTorch model from Detectron2's model zoo:
`model_final_f6e8b1.pkl: 243MB [01:13, 3.32MB/s]`

2) When ready, it will listen on port 50051:
`AIP inference server listening on [::]:50051`

3) It logs the `ConfigurationRequest` (after the aip-orchestrator is up and running in Step 5)
`Received configuration request from AIP Orchestrator:<version id>`

4) Then, on every `InferenceRequest` (after the aip-orchestrator is up and running in Step 5)
```
Received Infer request from AIP...
Reading image at: <image path>
Predicting on image...
Sending InferenceResponse.
```

### 4) [Download](https://repo1.maven.org/maven2/com/palantir/aip/processing/aip-test-orchestrator/v1.4/aip-test-orchestrator-v1.4.tar) and run the `aip-test-orchestrator`

The `aip-test-orchestrator` is a really simple AIP simulator that repeatedly sends the same image to the processor. Use it liberally
to ensure that your processor receives requests correctly, responds to them in the right format, and can handle large loads
without crashing.

First, extract the test orchestrator from the .tar file:
```bash
tar -xvf aip-test-orchestrator-<version>.tar
```

Then, run it with the following command:
```bash
cd aip-test-orchestrator-<version>
./bin/aip-test-orchestrator
```

#### Optional flags
```
--shared-images-dir (default /tmp): The directory path that frames should be written to and shared with the processor.
--uri (default grpc://localhost:50051): The URI of the inference processor to connect to.
--rate (default 0.2): The number of frames per second to send to the processor (can be a decimal).
```

#### Expected print statements
```
Orchestrator: running
Frames per second: <rate>
Sending configuration request to server...
SLF4J: Failed to load class "org.slf4j.impl.StaticLoggerBinder".
SLF4J: Defaulting to no-operation (NOP) logger implementation
SLF4J: See http://www.slf4j.org/codes.html#StaticLoggerBinder for further details.
Processor configured. Getting ready to send inference requests.
Created test image at location:<path to test image>
Orchestrator: sending task...
```

Then, it starts sending `InferenceRequest`s to the running processor (from Step 4).

For each `InferenceResponse` received from the processor:
```
Orchestrator received inference response for frame id <frame id>:
<list of inferences>
----------- End response for frame id <frame id> -----------
```

## Jetson processor

### 1) Clone the AIP SDK source code from the [Github repository](https://github.com/palantir/aip-sdk)
Note: Please make sure GIT LFS is installed when cloning. More information on the
[official website](https://git-lfs.github.com/) of git-lfs.
### 2) Build the processor (will take a while)

For Jetson 4.3:
```bash
./build_image.sh -f Dockerfile.jetson43 -t myjetsonprocessor:1.0.0
```

For Jetson 4.6:
```bash
./build_image.sh -f Dockerfile.jetson46 -t myjetsonprocessor:1.0.0
```

### 3) Test the processor
```bash
./test_jetson_inference.sh -t myjetsonprocessor:1.0.0
```

This will perform inference a few times on a test image and print the output predictions and inference times.

### 4) Run the processor on port 50051 (default)
```bash
./start_jetson_container.sh -t myjetsonprocessor:1.0.0
```

Once it has successfully started, you can use the real AIP to send it requests. The jetson processor does not work with the orchestrator.

