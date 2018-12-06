# -*- encoding: utf-8 -*-
'''
用来解析html文档的内容
标题中的% .会被删除
'''
import re
import sys
import time
import cProfile
import requests
import traceback

from lxml import etree
from scipy.signal import tukey
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime
from urllib.parse import urljoin

class HTMLTree:
    def __init__(self, url, html, strip=True, features='lxml', **kwargs):
        assert(isinstance(html, str))
        self.url = url
        self.html = html
        if strip:
            self.html = re.sub(r'\s\s+', ' ', self.html)
            self.html = re.sub(r'\n+', '', self.html)
        self.text_decoration_tag = {'strong', 'i', 'em', 'b', 'u', 'span'}
        self.remove_list = ['script', 'style', 'img', 'a']
        parser = etree.HTMLParser(remove_comments=True)
        self.htmltree = etree.fromstring(self.html, parser=parser)
        self.num_h1 = len( self.htmltree.xpath('//h1') )
        self.num_href = len( self.htmltree.xpath('//*[@href]') )
        self.num_title = len( self.htmltree.xpath('//title') )
        self.num_author = ( 1 if self._extract_author_string() else 0 )
        self.num_date = ( 1 if self._extract_date_string() else 0 )
        # print(self.num_h1,  self.num_href)
        # print('With style&script', len(etree.tostring(self.htmltree)))
        self._remove_all()
        # print('Without style&script&links&attr&nulls', len(etree.tostring(self.htmltree)))
        # print("===========================")
        # print(etree.tostring(self.htmltree))
        # print("===========================")
        # print(self._extract_str())
        self.maxlen, self.sumlen = self._extract_str()

    def _extract_str(self):
        content = ""
        sumlen, maxlen = 0, 0
        for e in self.htmltree.xpath('//*'):
            if (e.text != None and len(e.text.strip()) >= 30) :
                content += e.text.strip()
                sumlen += len(e.text.strip())
                maxlen = max(maxlen, len(e.text.strip()))
                # print(e.text.strip(), len(e.text.strip()))
            if (e.tail != None and len(e.tail.strip()) >= 30) :
                content += e.tail.strip()
                sumlen += len(e.tail.strip())
                maxlen = max(maxlen, len(e.tail.strip()))
                # print(e.tail.strip(), len(e.tail.strip()))
        return maxlen, sumlen

    def _remove_all(self):
        self._remove_detail()
        # remove link
        for e in self.htmltree.xpath('//*[@href]'):
            e.getparent().remove(e)
        # delete the list of <links and text> when structure is still here
        # self._remove_list()
        # remove null & leaf tag-node in tree
        tag = 1
        while tag == 1:
            tag = 0
            for e in self.htmltree.xpath('//*'):
                if ( len(e.getchildren()) == 0 and (e.text == None or len(e.text.strip()) <= 30) \
                and (e.tail == None or len(e.tail.strip()) == 0) ) and e.getparent() != None :
                    tag = 1
                    e.getparent().remove(e)

    def _remove_detail(self):
        for element in self.htmltree.xpath('//*'):
            # 不要style和script类型的tag
            if element.tag in self.remove_list and element.getparent() != None:
                element.getparent().remove(element)
                return False
            # 删除tag中的style属性
            elif element.get('style'):
                del element.attrib['style']
                return True
            # 删除comment
            elif element.tag is etree.Comment:
                print("comment: ===============")
                print(etree.tostring(element))
                element.getparent().remove(element)
                return False
            return True

        # I don't want hrefs in <script>
        self.num_href = len( self.htmltree.xpath('//*[@href]') )

        # extract some meta data before this, html structure is destroyed since 
        self.remove_list = ['head', 'li', 'ul']
        for e in self.htmltree.xpath('//*'):
            if element.tag in self.remove_list and element.getparent() != None:
                element.getparent().remove(element)
                return False

    def _extract_date_string(self, title_element=None, content_element=None):
        '''
        提取日期, 通常日期位于 title 和 content 之间.
        如果用户没有指定title_element 和 content_element, 就全文匹配.
        '''
        pattern_time = re.compile(r'(\d{2,4}\s*[年\-:/]\s*)\d{1,2}\s*[月\-：/]\s*\d{1,2}\s*[\-_:/日]?\s*([0-9]|0[0-9]|1[0-9]|2[0-3]):  [0-5][0-9](:[0-5][0-9])?')
        pattern_date = re.compile(r'(\d{2,4}\s*[年\-:/]\s*)\d{1,2}\s*[月\-：/]\s*\d{1,2}\s*[\-_:/日]?')
        pattern_year_month_day = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}')

        date = []
        for node in self.htmltree.xpath('//*'):
            # extract text
            if node.text == None and node.tail == None:
                continue
            text = node.text
            if node.tail != None:
                text = node.tail
            text_len = len(text)
            # 过长的文本中不太可能包含发表日期
            if (text_len < 5 or text_len > 32) and '时间' not in text and '日期' not in text and '年' not in text and '月' not in text and '日' not in text and not pattern_year_month_day.search(text):
                continue
            pub_time = pattern_time.search(text)
            pub_date = pattern_date.search(text)
            if pub_time or pub_date:
                return 1
        return 0


    def _extract_author_string(self):
        '''
        提取作者, 通常日期位于 title 和 content 之间. 少数情况下位于content之后
        如果用户没有指定 title_element 和 content_element, 就全文匹配.
        为保证正确性, 只提取包含"作者:" 或 "记者:"前缀的
        '''
        pattern_author = re.compile(r'(作者|记者|发布人)\s*[ :：]\s*([\sa-zA-Z\u4E00-\u9FFF]+)')
        pattern_author_prefix = re.compile(r'(作者|记者|发布人)\s*[ :：]\s*')

        authors = []
        for node in self.htmltree.xpath('//*'):
            # extract text
            if node.text == None and node.tail == None:
                continue
            text = node.text
            if node.tail != None:
                text = node.tail

            text_len = len(text)
            # 过长的文本中不太可能包含作者信息
            if text_len <= 2 or text_len >= 30 and '作者' not in text:
                continue
            match = pattern_author_prefix.search(text)
            if match:
                authors.append('get')
                return authors
        return authors

def bytes_to_html(content):
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

# for test
if __name__ == '__main__':
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
    resp = requests.get(sys.argv[1], headers=headers)
    resp.encoding = 'utf-8';
    page = bytes_to_html(resp.content)
    tree = HTMLTree(resp.url, page, features='lxml')

    print(resp.url)


