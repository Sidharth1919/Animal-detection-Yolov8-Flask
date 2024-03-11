# importing libraries
from flask import Flask, render_template, Response, request
import cv2
import os
import signal
from ultralytics import YOLO
import numpy as np
import pandas as pd

# global variables
count_var = 0
animal_type = "none"
threat_type = "none"
detection_list = []
csv_str = "none"


# creating flask app
app = Flask(__name__)

# home route
@app.route("/")
def index():
    return render_template('index.html')

VIDEO_FILE_PATH = "test2.mp4"  


def generate_frames(input_source):

    # access the global variable
    global count_var
    global animal_type
    global threat_type
    global detection_list
    global csv_str
    model = YOLO("yolov8n.pt")

    if input_source == 0:  # Webcam
        cap = cv2.VideoCapture(0)
    elif input_source == 1:  # Video file
        cap = cv2.VideoCapture(VIDEO_FILE_PATH)
    else:
        return  # Invalid input source - Handle this in the route

    if not cap.isOpened():
        print("Error opening video stream or file")
        return  # Handle error - return error response in route
    while True:

        # ---------- capturing frames-----------#
        ret , frame = cap.read()
        if not ret :
            break

        # ---------- resizing the frames---------#
        frame = cv2.resize(frame , (1400,800))

        # --------- list that stores the centroids of the current frame---------#
        centr_pt_cur_fr = []

        results = model(frame)
        result = results[0]
        # print("this is shape of frame,",frame.shape)
        # print("this is result :")
        # print(result)

        # ------- to get the classes of the yolo model to filter out the people---------------#
        classes = np.array(result.boxes.cls.cpu(),dtype="int")
        print("this is classes:",classes)

        # ---------confidence level of detections-----------#
        confidence = np.array(result.boxes.conf.cpu())
        print("this is confidence:",confidence)

        # --------- anarray of bounding boxes---------------#
        bboxes = np.array(result.boxes.xyxy.cpu(),dtype="int")
        print("this is boxes",bboxes)

        # -------- getting indexes of the detections containing animals--------#
        idx = []
        for i in range(0, len(classes)):
            if classes[i] in [0, 18, 19]:  
                idx.append(i)

        cls=classes.tolist() # detected class id tensor to list
        print("this is cls:",cls)
        cls_set=set(cls) # unique classes

        names=model.names #dict of classes

        # --------- testing detection----------#
        detection_list = [] # list to store the detected classes
        for i in cls_set:
            if i in names:
                detection_list.append(names[i])
        print("this is detection_list:",detection_list)
        csv_str = ', '.join(detection_list)
        print("this is string of detections:",csv_str)
        print("----------------------------------------------------------")
        # -------------------------------------#

        for r in results:
            for c in r.boxes.cls:
                if int(c) in [0, 18, 19]:
                    animal_type = names[int(c)]
                    print("this is animal type:",animal_type)


        if animal_type == "cow":
            if 0 in cls:
                print("kcbckdbckdbckdbckdbckdbcjkdbcjkdbcdcdncdkhcbdckbkjdbckdbjkd")
                threat_type = "Person"


        print("these are indexes:",idx)

        # ----------- bounding boxes for animal detections---------------#
        bbox = [] 
        for i in idx:
            temp = bboxes[i]
            print ("this is temp",temp)
            bbox.append(temp)
        
        # Convert to bbox to multidimensional list
        box_multi_list = [arr.tolist() for arr in bbox]
        print("this are final human detected boxes")
        print(box_multi_list)    

        # ------------ drawing of bounding boxes-------------#
        for box in box_multi_list :
            (x,y,x2,y2) = box
            
            cv2.rectangle(frame,(x,y),(x2,y2),(0,0,255),2)
            cx = int((x+x2)/2)
            cy = int((y+y2)/2)
            centr_pt_cur_fr.append((cx,cy))
            cv2.circle(frame,(cx,cy),5,(0,0,255),-1)

    

        print("this are the centroids in the current frame")
        print(centr_pt_cur_fr)

        # ------------- counting of total no of animals in the footage ------------# 
        animal_count = len(centr_pt_cur_fr)

        # counting the number of animals with count_var variable
        count_var = animal_count

        # displaying the count on the screen
        cv2.putText(frame, f'Animals: {animal_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Type: {animal_type}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)


        # if the q is pressed the the loop is broken
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        # Convert the frame to JPEG and yeild it
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()


# video feed route
@app.route("/video_feed")
def video_feed():
    ip_address = request.args.get('ip')
    try:
        ip_address = int(ip_address)
    except ValueError:
        return "Invalid IP address, please enter 0 or 1"

    return Response(generate_frames(ip_address), mimetype='multipart/x-mixed-replace; boundary=frame')
    
# video stop feed route
@app.route("/stop_feed")
def stop_feed():
    os.kill(os.getpid(), signal.SIGINT)
    return "feed stopped!"

# face count route
@app.route("/count")
def count():
    return str(count_var)

@app.route("/type")
def type():
    return str(animal_type)

@app.route("/detections")
def detections():
    return str(csv_str)

@app.route("/threat")
def threat():
    return str(threat_type)

# farm route
@app.route("/farm", methods = ['GET', 'POST'])
def farm():

    # logic for input field validation
    if request.method == 'POST':
        
        if (request.form['ip'] == ''):
            inv_feed ="No Video-Feed!"
            return render_template('farm.html',var2 = inv_feed)
        
        else:
            ip_address = request.form['ip']
            ip_vd_feed = "Video-Feed"
            return render_template('farm.html', ip_address = ip_address, var2 = ip_vd_feed)
    
    if request.method == 'GET':
        return render_template('farm.html')


if __name__ == '__main__':
    app.run(debug=True, port=8000)