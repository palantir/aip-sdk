usage() { echo "Usage: $0 [-t <image tag name:version>] [Additional python arguments]" 1>&2; exit 1; }


while getopts :t: flag
do
    case "${flag}" in
        t) t=${OPTARG};;
    esac
done

if [ -z "${t}" ]
  then
    usage
fi

sudo docker run -v /usr/local/cuda-10.0:/usr/local/cuda-10.0 -v /usr/lib/aarch64-linux-gnu/tegra:/usr/lib/aarch64-linux-gnu/tegra -v /usr/local/cuda-10.0/targets/aarch64-linux/lib:/usr/local/cuda-10.0/targets/aarch64-linux/lib -v /tmp:/tmp -v /dev/shm/aip/images:/dev/shm/aip/images --rm --device=/dev/nvhost-ctrl  --device=/dev/nvhost-ctrl-gpu  --device=/dev/nvhost-prof-gpu  --device=/dev/nvmap  --device=/dev/nvhost-gpu  --device=/dev/nvhost-as-gpu --runtime=nvidia --network=host -it "${t}" "inference_server.py" ${@: 3}
