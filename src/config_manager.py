# encoding: utf-8
"""
@author: hechenrui
@contact: hechenrui123@gmail.com

@version: 1.0
@file: settints_manager.py
@time: 2018-11-30 15:37

配置管理器
"""

import os
import yaml


class _SettingManager(object):

    def __init__(self):
        self.PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))  # __file__是相对路径
        self.LOG_FILE_DIR = os.path.join(self.PROJECT_PATH, '/../log')

        # 从yaml文件读取的配置
        yaml_file_path = self.PROJECT_PATH+"/../conf/config.yaml"
        if not os.path.exists(yaml_file_path):
            raise FileNotFoundError('Configuration file "{}" is not found!'.format(yaml_file_path))

        yaml_config_dict = yaml.load(open(yaml_file_path, encoding="utf8"))

        self.MODEL = yaml_config_dict.get("model", "svm")
        self.DATASET = yaml_config_dict.get("dataSet", "/../data/tagged_pages.csv")
        self.DATASET = os.path.join(self.PROJECT_PATH, self.DATASET)
        features = {'paragraphLength': True, \
                    'paragraphPercentage': False, \
                    'linkNumber': False, \
                    'linkPercentage': False, \
                    'titleLength': False, \
                    'URLPostfix': []}
        self.FEATURES = yaml_config_dict.get("features", features)
        self.URLPOSTFIX = self.FEATURES["URLPostfix"]

# 全局唯一配置管理访问器
config = _SettingManager()
