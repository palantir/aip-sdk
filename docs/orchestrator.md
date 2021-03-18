Build Docker image: `docker build -t <image name>:<image version> .`
Run Docker container: `docker run -it --rm -v /tmp:/tmp -p 50051:50051 <image name>:<image version>`

Expected prints after successful initialization:

It will download a PyTorch model from Detectron2's model zoo:
`model_final_f6e8b1.pkl: 243MB [01:13, 3.32MB/s]`

When ready, it will listen on port 50051:
`AIP inference server listening on [::]:50051`

When the orchestrator has started, it will send a configuration request to the processor, which will result in a print like this:
`Received configuration request from AIP Orchestrator:<version id>`

As the orchestrator sends images at a regular cadence, the processor prints the following on each request:
```
Received Infer request from AIP...
Reading image at: <image path>
Predicting on image...
Sending InferenceResponse.
```

Notes:

```
-v /tmp:/tmp mounts the hosts "/tmp" folder to "/tmp" in the container. It is the default location where aip orchestrator saves images for the processor to read from. The directory can be changed by specifying the --images-dir flag when running the aip-orchestrator. Just remember to mount that folder here so the processor can read images!
-p 50051:50051 makes port 50051 in the container listen to port 50051 on the host. The aip orchestrator will send requests to port 50051, which will make its way into the container and reach the processor listening on the same port.
--rm will delete the container once it has exited.
```
