FROM nvcr.io/nvidia/pytorch:20.03-py3

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq \
  && apt-get install -y apt-utils \
  && apt-get upgrade -y \
  && apt-get install -y python3-pip python3-tk \
  && apt-get install -y \
      build-essential \
      clang \
      libpython3-dev \
      libblocksruntime-dev \
      libpython3.6 \
      libxml2 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /test-harness/

EXPOSE 50051

COPY model/ ./model/

COPY resources/ ./resources/
RUN source resources/install-python-packages.sh

COPY proto/ ./proto/
COPY generate_protos.sh .
RUN ./generate_protos.sh

COPY inference_server.py .
CMD ["python3", "inference_server.py", "50051"]
