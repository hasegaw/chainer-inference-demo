#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import random
import re
import sys
import threading
import time

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template

import numpy as np
from PIL import Image

import chainer

websockets = []
samples = []
parser = argparse.ArgumentParser()

parser.add_argument('--gpu', type=int, default=-1)
parser.add_argument('--batchsize', type=int, default=10)

args = parser.parse_args()


def read_filenames(path):
    l = []
    filenames = []

    for root, dirs, files in os.walk(path):
        for filename in sorted(files):
            if filename.endswith(".jpg"):
                f = os.path.join(root, filename)
                filenames.append(f)
                continue

    return filenames


def read_samples(filenames):
    samples = []
    for filename in filenames:
        s = {
            'filename': filename,
            'img_rgb': Image.open(filename).copy(),
        }
        samples.append(s)
    return samples


if __name__ == "__main__":
    write_console = True

    filenames = read_filenames('101_ObjectCategories')
    samples = read_samples(filenames)

    labels = open('data/synset_words.txt').readlines()
    labels_simple = list(map(lambda x: re.match(
        r'\S+ ([^,\n]+)', x).group(1), labels))

    #model = chainer.links.GoogLeNet()
    model = chainer.links.VGG16Layers()
    # model = chainer.links.ResNet152Layers()

    if args.gpu >= 0:
        # Make a specified GPU current
        chainer.cuda.get_device_from_id(args.gpu).use()
        model.to_gpu()  # Copy the model to the GPU
        #print('gpu = %d' % args.gpu)

    sys.stdout.flush()

    while True:

        x_list = []
        filename_list = []
        for i in range(args.batchsize):
            n = int(random.random() * len(samples))
            x_list.append(samples[n].get('img_rgb'))
            filename_list.append(samples[n]['filename'])
        var_y = model.predict(x_list)

        if args.gpu >= 0:
            cpu_y = chainer.cuda.to_cpu(var_y.data)
        else:
            cpu_y = var_y.data
        for i in range(len(x_list)):
            filename = filename_list[i]
            y = cpu_y[i]
            cls_id = int(np.argmax(y))
            label = labels[cls_id]

            y_label = list(zip(y, labels_simple))
            y_label_top5 = sorted(y_label, key=lambda x: -x[0])[:5]
            if 1:
                label_top5 = list(map(lambda y: y[1], y_label_top5))
                y_top5 = list(map(lambda y: float(y[0]), y_label_top5))
                y_label_top5 = list(zip(label_top5, y_top5))

            if 0:
                """
                Softmax で確率に落とし込む... あまり見栄えがしない
                """
                sum_votes_exp = np.sum(np.exp(y))
                y_acc = list(
                    map(lambda y: float(np.exp(y) / sum_votes_exp), y_top5))
                y_label_top5 = list(zip(label_top5, y_acc))

            if 0:
                print(y_label_top5)
                print(filename, cls_id, labels[cls_id])

            ws_data = [{'filename': filename, 'p': y_label_top5}]

            if write_console:
                print(json.dumps(ws_data))
                sys.stdout.flush()

#        if write_console:
