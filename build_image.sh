usage() { echo "Usage: $0 [-f <dockerfile path>] [-t <output image tag name:version>]" 1>&2; exit 1; }

while getopts f:t: flag
do
    case "${flag}" in
        f) f=${OPTARG};;
        t) t=${OPTARG};;
    esac
done

if [ -z "${f}" ] || [ -z "${t}" ]
  then
    usage
fi

sudo docker build --network host . -f "${f}" -t "${t}"
