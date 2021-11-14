import cv2
import sys
import datetime
import time
import numpy as np
from PIL import Image   
import os
from detectron2.config import get_cfg
from detectron2.engine import(
     DefaultPredictor
)
import torch
import copy
from PIL import Image
def load_mask(image,dataset_dict):
    """Generate instance masks for the objects in the image with the given ID.
    """
    #masks, coords, class_ids, scales, domain_label = None, None, None, None, None
    
    image = image.copy()
    id = dataset_dict["id"]
    image_id = dataset_dict["image_id"]
    gt_dir = os.path.join("/data2","qiweili","cat","gt",str(id),image_id+'.png')
    #print(gt_dir)
    mask = cv2.imread(gt_dir )[:, :, :3]#本来就二维，第三个2的参数可以去掉 

    return image , mask 


j = 0
def file_name(file_dir):
    list_dir = []
    for _, _, files in os.walk(file_dir):  
        list_dir =files #当前路径下所有非目录子文件 
    return list_dir
def cat_train_function( ):
    """Load a subset of the CAMERA dataset.
    dataset_dir: The root directory of the CAMERA dataset.
    subset: What to load (train, val)
    if_calculate_mean: if calculate the mean color of the images in this dataset
    """
    global j 
    print('begin load cat')
    dataset_dir = os.path.join("/data2","qiweili","cat","train")
    folder_list = [name for name in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, name))]
    list = []
    for i in range(1,len(folder_list)+1):
        cat_id = i 
        cat_dir = os.path.join(dataset_dir,str(i))
        image_path_all =file_name(cat_dir)
        for i in range(len(image_path_all)) :
            image_path = os.path.join(cat_dir,image_path_all[i])
            t = image_path_all[i]
            t = t.split('.')[0]
            list.append({'image_id':t,'image_path':image_path,
                            'id':cat_id})
            j=j+1
    
    print(j)
    print('load cat successfully')
    return list

def mapper(dataset_dict):
    #print(dataset_dict)

    #time.sleep(1)
    #print('use mapper')
    dataset_dict = copy.deepcopy(dataset_dict)  # it will be modified by code below

    image_path = dataset_dict["image_path"]
    #print(image_dir)
    #print(image_dir)

    image = cv2.imread(image_path)[:, :, :3]
    
    #image = image[:, :, ::-1]
    #image_d = image[:, :, ::-1].copy()
    # If grayscale. Convert to RGB for consistency.
    #cv2.imwrite('origin.jpg',image)
    if image.ndim != 3:
        image =  cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

  
    image ,mask= load_mask(image,dataset_dict)

    return image,mask 

if __name__ == "__main__":
    name = {"1":"杜若",
        "2":"小宝",
        "3":"雪风",
        "4":"塵尾"}
    
    if hasattr(torch.cuda, 'empty_cache'):
        torch.cuda.empty_cache()
    cfg = get_cfg()
    cfg.MODEL.DEVICE = "cpu"
    cfg.DATALOADER.ASPECT_RATIO_GROUPING = False
    cfg.merge_from_file(
        "configs/mask_rcnn_R_50_FPN_3x.yaml"
    )
    cfg.DATALOADER.NUM_WORKERS = 0


    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

    

    cfg.MODEL.WEIGHTS = os.path.join("/data2/qiweili/logs/cat", "model_0009999.pth") 

    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5 # 设置一个阈值
    predictor = DefaultPredictor(cfg)
    #print('model built',flush=True)
    #image =cv2.imread("3.png")

    image =np.array(Image.open("3.png").convert("RGB"))[:,:,::-1]
    print(image.shape)
    image = image.copy()
    out = predictor(image)
    bbox=out["instances"].pred_boxes.tensor.int().cpu().numpy()
    #print(bbox)
    print('\n\n\n\n\n\n\n\n\n\n')
    print('cat is',name[str(out["instances"].pred_classes.cpu().numpy()[0])])
    print('scores:',out["instances"].scores.cpu().numpy()[0])
    #image = image[:,:,::-1].copy()
    for i in range(len(bbox)):
        cv2.rectangle(np.ascontiguousarray(image), (bbox[i][0], bbox[i][1]), (bbox[i][2], bbox[i][3]),
                    color=(0,0,255), thickness = 10 )
    cv2.imwrite('after.jpg',image)

def run(conn) :
    #print(q)
    name = {"1":"杜若",
        "2":"小宝",
        "3":"雪风",
        "4":"塵尾"}
    
    cfg = get_cfg()

    cfg.DATALOADER.ASPECT_RATIO_GROUPING = False
    cfg.merge_from_file(
        "/home/meoknow/detectron2/configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
    )
    #cfg.DATALOADER.NUM_WORKERS = 0


    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    cfg.MODEL.DEVICE = "cpu"

    

    cfg.MODEL.WEIGHTS = os.path.join("/home/meoknow/logs", "model_0009999.pth") 

    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5 # 设置一个阈值
    predictor = DefaultPredictor(cfg)
    #print('model built',flush=True)
    #image =cv2.imread("3.png") 
    while 1 :
        dict={"cat":[],"score":[],"error":[]}
        img = conn.recv()

        try :
            image =np.array(Image.open(img).convert("RGB"))[:,:,::-1]
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

        #image =np.array(Image.open(img).convert("RGB"))[:,:,::-1]
        #print(image.shape,flush=True)
        image = image.copy()
        out = predictor(image)
        bbox=out["instances"].pred_boxes.tensor.int().cpu().numpy()
        #print(bbox)
        #print('\n\n\n\n\n\n\n\n\n\n',flush=True)

        #print('cat is',name[str(out["instances"].pred_classes.cpu().numpy()[0])],flush=True)
        dict["cat"].append(name[str(out["instances"].pred_classes.cpu().numpy()[0])])
        dict["score"].append(out["instances"].scores.cpu().numpy()[0])
        conn.send(dict)
        #return_dict.append(dict)
        #return_dict.append(name[str(out["instances"].pred_classes.cpu().numpy()[0])])
        #print('scores:',out["instances"].scores.cpu().numpy()[0],flush=True)
        #image = image[:,:,::-1].copy()
        '''
        for i in range(len(bbox)):
            cv2.rectangle(np.ascontiguousarray(image), (bbox[i][0], bbox[i][1]), (bbox[i][2], bbox[i][3]),
                        color=(0,0,255), thickness = 10 )
        cv2.imwrite('after.jpg',image)
        '''
        #print(11)


