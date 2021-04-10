# Quickstart

## 1) Clone the AIP SDK source code from the [Github repository](https://github.palantir.build/video/aip-sdk).

## 2) Download the public AIP Protocol Buffer interface files from [Bintray](https://bintray.com/palantir/releases/aip-processor-api).
The latest version is `0.0.2`.

Extract the contents of the tarball using the following command:
```bash
tar -xzvf <name of tar>
```

Copy `processing-service-v2.proto` and `configuration-service.proto` into the `proto` folder of the repository:
```
cp processing-service-v2.proto <path to aip-sdk repository>/proto/
cp configuration-service.proto <path to aip-sdk repository>/proto/
```

You **do not** need to manually compile these proto files. Building the docker image in Step 3 (see next step) will
automatically compile it, and save the resulting .py files inside the image.

## 3) Now you're ready to build the sample processor! Build the docker image using the following command:
```bash
cd <path to aip-sdk repository>
docker build --no-cache -t testplanemodel:1.0.0 .
```

## 4) Run the docker image with the following flags. This will start a processor on port 50051.
```bash
docker run -it --rm -v /tmp:/tmp -p 50051:50051 testplanemodel:1.0.0
```

### Understanding the flags
```
Required:
-v /tmp:/tmp mounts the hosts "/tmp" folder to "/tmp" in the container. It is the default location where aip orchestrator saves images for the processor to read from. The directory can be changed by specifying the --images-dir flag when running the aip-orchestrator. Just remember to mount that folder here so the processor can read images!
-p 50051:50051 makes port 50051 in the container listen to port 50051 on the host. The aip orchestrator will send requests to port 50051, which will make its way into the container and reach the processor listening on the same port.

Optional but highly recommended:
--rm will delete the container once it has exited.
```

### Expected prints after successful initialization

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

## 5) [Download](https://publish.artifactory.palantir.build/ui/repos/tree/General/internal-dist-snapshot%2Fcom%2Fpalantir%2Faip%2Faip-orchestrator%2F1.35.0-19-ge15c432%2Faip-orchestrator-1.35.0-19-ge15c432.tgz) and run the `aip-orchestrator`

The `aip-orchestrator` is a really simple AIP simulator that repeatedly sends the same image to the processor. Use it liberally
to ensure that your processor receives requests correctly, responds to them in the right format, and can handle large loads
without crashing.

First, extract the orchestrator from the .tgz file:
```bash
tar -xvzf aip-orchestrator-<version id and checksum>.tgz
```

Then, run it with the following command:
```bash
./aip-orchestrator-<version id and checksum>/bin/aip-orchestrator
```

### Optional flags
```
--shared-images-dir (default /tmp): The directory path that frames should be written to and shared with the processor.
--uri (default grpc://localhost:50051): The URI of the inference processor to connect to.
--rate (default 0.2): The number of frames per second to send to the processor (can be a decimal).
```

### Expected print statements
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
