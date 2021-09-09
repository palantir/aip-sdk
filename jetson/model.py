import numpy as np
import tensorflow as tf


class InferenceModel(object):
    def __init__(self, frozen_graph_path):
        graph, inp, sess = self.load_inference_graph(frozen_graph_path)
        self.graph = graph
        self.detection_boxes = self.graph.get_tensor_by_name(
            "detection_boxes:0")
        self.detection_classes = self.graph.get_tensor_by_name(
            "detection_classes:0")
        self.detection_scores = self.graph.get_tensor_by_name(
            "detection_scores:0")
        self.inp = inp
        self.sess = sess

    def load_inference_graph(self, inference_graph_path, is_binary=True):
        print("Loading inference graph...")
        od_graph = tf.Graph()
        with od_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(inference_graph_path, mode='rb') as fid:
                if is_binary:
                    od_graph_def.ParseFromString(fid.read())
                # expecting 3-channel RGB images
                inp = tf.placeholder(
                    np.uint8, shape=[None, None, None, 3], name='image_tensor')
                tf.import_graph_def(
                    od_graph_def, {'image_tensor': inp}, name='')
        sess = tf.Session(graph=od_graph)
        print("Loaded inference graph.")
        return od_graph, inp, sess

    def run_inference(self, image):
        print("Running inference...")
        detection_boxes, detection_classes, detection_scores = self.sess.run(
            [self.detection_boxes,
                self.detection_classes,
                self.detection_scores],
            feed_dict={self.inp: [image]})
        print("Inference completed.")
        return {
            "detection_boxes": detection_boxes,
            "detection_classes": detection_classes,
            "detection_scores": detection_scores
        }
