usage() { echo "Usage: $0 [-t <image tag name:version>]" 1>&2; exit 1; }

while getopts t: flag
do
    case "${flag}" in
        t) t=${OPTARG};;
    esac
done

if [ -z "${t}" ]
  then
    usage
fi

sudo docker run -v /usr:/usr -v /tmp:/tmp -v /dev/shm/aip/images:/dev/shm/aip/images --rm --device=/dev/nvhost-ctrl  --device=/dev/nvhost-ctrl-gpu  --device=/dev/nvhost-prof-gpu  --device=/dev/nvmap  --device=/dev/nvhost-gpu  --device=/dev/nvhost-as-gpu --runtime=nvidia --network=host -it "${t}" python3 test_model.py
