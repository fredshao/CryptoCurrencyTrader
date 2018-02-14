# -*- coding: utf-8 -*-

import os

def AppendTextToFile(fileName,text):
    """
    追加文本
    """
    with open(fileName,'a') as f:
        f.write(text + '\n')

def WriteTextToFile(fileName, text):
    """
    写入文本
    """
    with open(fileName,'w') as f:
        f.write(text)

def ReadTextFromFile(fileName):
    """
    读取文件
    """
    if not os.path.exists(fileName):
        return None
    with open(fileName,'r') as f:
        return f.read()
        
def AppendBinaryToFile(fileName,data):
    """
    追加二进制
    """
    with open(fileName,'ab') as f:
        f.write(data)

def WriteBinaryToFile(fileName, data):
    """
    写入二进制
    """
    with open(fileName,'wb') as f:
        f.write(data)

def ReadBinaryFromFile(fileName):
    """
    读取二进制
    """
    with open(fileName,'rb') as f:
        return f.read()