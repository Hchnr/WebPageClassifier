# encoding: utf-8
"""
@author: hechenrui
@contact: hechenrui123@gmail.com

@version: 1.0
@file: train.py
@time: 2018-11-30 16:37

模型训练
"""

import os
import re
import yaml
import requests
import sys
import cProfile

import numpy as np
from sklearn import svm
from sklearn.externals import joblib
from sklearn.model_selection import KFold

from config_manager import config
from resolve_html import HTMLTree
from process_data import Processor


if __name__ == '__main__':
    print("Original Data Set:\n", config.DATASET)
    prc = Processor()
    X, y = prc.getData()
    # rawX, rawy = prc.getData()
    # X, y = NormData(rawX, rawy)
    N, s = 1, 0
    for i in range(N):
        kf = KFold(n_splits=2, shuffle=True)
        # 打印出每次训练集和验证集
        for train,test in kf.split(X):
            print(train, '\n', test)
            print("data: =========")
            # print(np.array(X)[train], '\n', np.array(X)[test])
            # print(np.array(y)[train], '\n', np.array(y)[test])
            clf = svm.SVC(kernel='linear', C=1)
            clf.fit(np.array(X)[train], np.array(y)[train])
            print(clf.score(np.array(X)[test], np.array(y)[test]))
            s += clf.score(np.array(X)[test], np.array(y)[test])
    print(s/N*100/2)


