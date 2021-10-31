from PIL import Image 
import numpy as np 
def run(conn) :

    while 1 :
        dict={"cat":[],"score":[],"error":[]}
        img = conn.recv()

        try :
            image =np.array(Image.open(img).convert("RGB"))[:,:,::-1]
        except FileNotFoundError as e :
            dict["error"].append('2')
            dict["error"].append(e)
            conn.send(dict)
            continue 
        except AttributeError as e :
            dict["error"].append('1')
            dict["error"].append(e)
            conn.send(dict)
            continue 
        except Exception as e :
            dict["error"].append('3')
            dict["error"].append(e)
            conn.send(dict)
            continue 
        dict = {'cat': ['对号'], 'score': [0.9975297], 'error': []}

        conn.send(dict)

