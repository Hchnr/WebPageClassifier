# encoding: utf-8
"""
@author: hechenrui
@contact: hechenrui123@gmail.com

@version: 1.0
@file: train.py
@time: 2018-11-30 16:37

数据预处理
"""

import os
import re
import sys
import yaml
import requests

import numpy as np
from sklearn import svm
from sklearn.externals import joblib
from sklearn.model_selection import KFold

from config_manager import config
from resolve_html import HTMLTree

class Processor:
    def __init__(self):
        # self.DEBUG = False
        self.DEBUG = True
        self.DOWNLOAD = False
        self.X = []
        self.y = []
        htmlDataPath = config.PROJECT_PATH + "/../data/rawHtml.npy"
        if not os.path.exists(htmlDataPath):
            raise FileNotFoundError('Raw html data "{}" is not found!'.format(htmlDataPath))
        self.raws = np.load(htmlDataPath)

    def bytes_to_html(self, content):
        match = re.search(rb'charset="?([A-Za-z0-9-]*)"?', content)
        html = None
        if match:
            encoding = match.group(1).decode('ascii')
            try:
                html = content.decode(encoding, 'ignore')
            except Exception as e:
                pass
        if html is None:
            try:
                html = content.decode('utf-8')
            except Exception as e:
                pass
        if html is None:
            try:
                html = content.decode('gb2312')
            except Exception as e:
                pass
        if html is None:
            try:
                html = content.decode('gbk')
            except Exception as e:
                pass
        return html

    def setHtmlData(self, link_datas):
        if os.path.exists('/../data/rawHtml.npy'):
            print("Raw HTML data file <./data/rawHtml.npy> already exist.")
        RAWHtml = []
        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3)\
                   AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

        if self.DEBUG:
            print("=======================\nHTML Data written: ")
            print("=======================")
        for link_data in link_datas:
            line = []
            try:
                resp = requests.get(link_data[0], headers=headers, timeout=0.8)
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
                continue
            page = self.bytes_to_html(resp.content)
            line.append(page)
            line.append(link_data[0])
            line.append(link_data[1])
            RAWHtml.append(line)
            if self.DEBUG:
                print("HTML Data writen: \n", line[1], line[2])
        np.save('../data/rawHtml.npy', RAWHtml)
        return True

    def getLinkData(self):
        if not os.path.exists(config.DATASET):
            raise FileNotFoundError('Raw link data "{}" is not found!'.format(config.DATASET))
        link_datas = np.loadtxt(config.DATASET, delimiter=",", dtype=np.str)
        if self.DEBUG:
            print("=======================\nLink Data Read: ")
            print(link_datas)
            print("=======================")
        return link_datas

    def addFeatures(self, x, raw):
        if not isinstance(raw[0], str):
            return False
        url = ""
        root = HTMLTree(url, raw[0])
        features = config.FEATURES

        if 'paraSumLength' in features.keys() and features['paraSumLength']:
            x.append(root.sumlen)
        if 'paraMaxLength' in features.keys() and features['paraMaxLength']:
            x.append(root.maxlen)
        if 'linkNumber' in features.keys() and features['linkNumber']:
            x.append(root.num_href)
        if 'paraSumLinkRatio' in features.keys() and features['paraSumLinkRatio']:
            x.append(root.sumlen / (root.num_href+1) )
        if 'paraMaxLinkRatio' in features.keys() and features['paraMaxLinkRatio']:
            x.append(root.maxlen / (root.num_href+1) )
        if 'isH1' in features.keys() and features['isH1']:
            x.append(root.num_h1)
        if 'isTitle' in features.keys() and features['isTitle']:
            x.append(root.num_title)
        if 'isAuthor' in features.keys() and features['isAuthor']:
            x.append(root.num_author)
        if 'isDate' in features.keys() and features['isDate']:
            x.append(root.num_date)

        return True

    def getFeaturedData(self):
        X = []
        y = []
        for raw in self.raws:
            x = []
            self.addFeatures(x, raw)
            if not x:
                continue
            X.append(x)
            y.append(raw[2])
            if self.DEBUG:
                print("======================\nAdded features: ")
                print(x, raw[2], raw[1])
                print("======================")
        self.X, self.y = X, y
        return X, y

    def getNormData(self):
        max_int = 100000
        # bot = [ sys.maxint for i in range(len(self.X[0]) - 1) ]
        bot = [ max_int for i in range(len(self.X[0]) - 1) ]
        top = [ 0 for i in range(len(bot))]
        for x in self.X:
            for i in range(len(top)):
                bot[i] = min(x[i], bot[i])
                top[i] = max(x[i], top[i])
        i = 0
        for x in self.X:
            for ii in range(len(top)):
                x[ii] = (x[ii] - bot[ii]) / (top[ii] - bot[ii])
            if x[-1] != 0:
                x[-1] = 1
            if self.DEBUG:
                print("======================\nNormaled features: ")
                print(x, self.raws[i][2], self.raws[i][1])
            i += 1


    def getData(self):
        self.DOWNLOAD = False
        self.DEBUG = True
        if self.DOWNLOAD:
            linkData = self.getLinkData()
            self.setHtmlData(linkData)
        self.getFeaturedData()
        self.getNormData()
        return self.X, self.y


def get_test():
    prc = Processor()
    prc.DEBUG = True
    print( "==================\nX, y:\n", prc.getData() )

if __name__ == '__main__':
    get_test()

