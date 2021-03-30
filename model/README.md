This folder contains the following model resources:

`Base-RCNN-FPN.yaml`:
Downloaded from [Detectron2 Base Configs](https://github.com/facebookresearch/detectron2/blob/master/configs/Base-RCNN-FPN.yaml)

`faster_rcnn_R_101_FPN_3x.yaml`:
Downloaded from [Detectron2 Model Configs](https://github.com/facebookresearch/detectron2/blob/master/configs/COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml)

`model_final_f6e8b1.pkl`:
Downloaded from [Detectron2 Faster-RCNN Model Zoo](https://github.com/facebookresearch/detectron2/blob/master/MODEL_ZOO.md#faster-r-cnn). This is a Faster R-CNN model with ResNet 101 and FPN, trained and evaluated on the COCO 2017 dataset. [COCO](https://cocodataset.org/) is a large-scale object detection, segmentation and captioning dataset, with 80 object categories, including aircrafts. For our sample Python processor, we care most about predictions for these classes: `Small Civil Transport/Utility`, `Medium Civil Transport/Utility`, `Large Civil Transport/Utility` (you will see these classes listed in `inference_server.py`).