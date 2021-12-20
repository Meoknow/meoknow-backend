#pridict.py

import torch
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
import json
#from ml_model import MobileNet
#from dataset import myDataset
import sys, os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "meoknow"))
import os 
import numpy as np
import cv2
import torch.nn as nn
import time 
from flask import current_app

def run(conn) :
    

        
    name = {"1":"杜若",
        "2":"小宝",
        "3":"雪风",
        "4":"塵尾",
        "5":"姜丝鸭",
        "6":"小尾巴"}

    model_weight_path = current_app.config.get("ML_LOG_PATH")

    #if os.path.exists(model_weight_path):
    #    print(1)
    #model.load_state_dict(torch.load(model_weight_path))
    model1 = torch.load(model_weight_path,map_location='cpu')
    data_transform = transforms.Compose(
            [
            transforms.Resize((224,224)),
            transforms.ToTensor()
            ])
    model1.eval()

    with torch.no_grad():
        while 1 :
            dict={"cat":[],"score":[],"error":[]}
            image_path = conn.recv()
            #print(image_path)
            try :
                img = Image.open(image_path)
            except FileNotFoundError as e :
                dict["error"].append('2')
                dict["error"].append(e)
                #return_dict.append(dict)
                conn.send(dict)
                continue 
            except AttributeError as e :
                dict["error"].append('1')
                dict["error"].append(e)
                #return_dict.append(dict)
                conn.send(dict)
                continue 
            except Exception as e :
                dict["error"].append('3')
                dict["error"].append(e)
                #return_dict.append(dict)
                conn.send(dict)
                continue 

            img = data_transform(img)[:3,:,:]

            img=img.unsqueeze(0)

            output = model1(img)
            output = output.squeeze(0)
            lsf = nn.Softmax()
            lsfout = lsf(output)

            a = lsfout.numpy()
            #print(a.argsort()[::-1]+1) #id
            #print(a[a.argsort()[::-1]]) #分数



            temp = []
            cls = a.argsort()[::-1]+1
            score = a[a.argsort()[::-1]]
            for i in range(3) :

                dict["cat"].append(name[str(cls[i])])
                dict["score"].append(score[i])
            conn.send(dict)







            
                