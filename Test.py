# -*- coding: utf-8 -*-

persions = {}

class Persion:
    def __init__(self,name,age):
        self.name = name
        self.age = age

    def DoChange(self):
        self.name = "haha"
        self.age = 18
        Save()


def Save():
    for key in persions:
        persion = persions[key]
        print(persion.name,persion.age)

persion = Persion("Fred",26)
persions[persion.name] = persion

persion.DoChange()
