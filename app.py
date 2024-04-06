# importing libraries
from flask import Flask, render_template, Response, request # importing flask library for web app (render_template for rendering html files, Response for streaming video, request for getting the input from the user)
from flask_socketio import SocketIO # importing socketio for real time communication between server and client
import cv2 # importing opencv for image processing
import os # importing os for killing the process
import signal # importing signal for killing the process
from ultralytics import YOLO # importing yolov8 for object detection
import numpy as np # importing numpy for numerical operations

# global variables
count_var = 0 # variable to store the count of animals
threat_type = "None" 
detection_list = [] # list to store the detected classes
csv_str = "none"
class_index = -1


# creating flask app
app = Flask(__name__)
socketio = SocketIO(app)

# home route
@app.route("/")
def index():
    return render_template('index.html')

# socketio event for updating the class from home page option
@socketio.on('update_class_index')
def handle_update_class_index(json):
    global class_index
    class_index = json.get('classIndex')
    print('received class index: ' + str(class_index))

@socketio.on('stop_feed')
def handle_stop_feed():
    os.kill(os.getpid(), signal.SIGINT)


VIDEO_FILE_PATH = "test2.mp4"  


def generate_frames(input_source):

    # access the global variable
    global count_var
    global threat_type
    global detection_list
    global csv_str
    model = YOLO("yolov8n.pt")

    if input_source == 0:  # Webcam
        cap = cv2.VideoCapture(0)
    elif input_source == 1:  # cam
        cap = cv2.VideoCapture('http://192.168.223.21:4747/video')
    elif input_source == 2:  # Video file
        cap = cv2.VideoCapture(VIDEO_FILE_PATH)
    else:
        return  # Handle error - TO DO
    
    if not cap.isOpened():
        print("Error opening video stream or file")
        return  # Handle error - TO DO
    while True:

        # ---------- capturing frames-----------#
        ret , frame = cap.read()
        if not ret :
            break

        # ---------- resizing the frames---------#
        frame = cv2.resize(frame , (1400,800))

        # --------- list that stores the centroids of the current frame---------#
        centr_pt_cur_fr = []

        results = model(frame) #Yolov8 model processes the frames
        result = results[0]

        # ------- to get the classes of the yolo model to filter out the animals---------------#
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
        int_index = int(class_index) # converting the class index to int
        # Appending only the indexes of the classes(farm) that are selected by the user in the home page
        for i in range(0, len(classes)):
            if classes[i] in [int_index]:  
                idx.append(i)
                print("this is idexes:",idx)


        cls=classes.tolist() # detected class id tensor to list
        print("this is cls:",cls)
        cls_set=set(cls) # unique classes
        cls_list=list(cls_set) # unique classes to list
        print(cls_list)

        names=model.names #dict of classes

        # ---------detection of the selected class only----------#
        detection_list = [] # list to store the detected classes
        for i in cls_set:
            if i in names:
                detection_list.append(names[i])
        print("this is detection_list:",detection_list)
        csv_str = ', '.join(detection_list)
        print("this is string of detections:",csv_str)
        print("----------------------------------------------------------")
        print(class_index)

        # detecting only the threat classes given#
        threat_types = []
        for i in cls_set:
            if i in [0, 16, 20, 21]:
                detected_threat = names.get(i, "Unknown")  # Use "Unknown" as a default if `i` is not in `names`
                if detected_threat not in threat_types:
                    threat_types.append(detected_threat)
                    print("this is threat detected:",detected_threat)

        threat_type = ", ".join(threat_types) if threat_types else "None"

        # ----------- bounding boxes for animal detections---------------#
        bbox = [] 
        for i in idx:
            temp = bboxes[i]
            print ("this is temp coordinates",temp)
            bbox.append(temp)
        
        # Convert to bbox to multidimensional list
        box_multi_list = [arr.tolist() for arr in bbox]
        print("these are the final animal detected boxes")
        print(box_multi_list)    

        # ------------ drawing of bounding boxes-------------#
        for box in box_multi_list :
            (x,y,x2,y2) = box
            #findng the center point of the bounding box
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

        # if the q is pressed the the loop is broken
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        # Convert the frame to JPEG and yeild it
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        emit_updates()
        print('emitted updates from function')
    


    cap.release()
    cv2.destroyAllWindows()


# video feed route
@app.route("/video_feed")
def video_feed():
    video_source = request.args.get('video_source')
    try:
        video_source = int(video_source)
    except ValueError:
        return "Invalid video source, please enter 0, 1, or 2"

    return Response(generate_frames(video_source), mimetype='multipart/x-mixed-replace; boundary=frame')


@socketio.on('send_updates')
def emit_updates():
    global count_var, csv_str, threat_type
    socketio.emit('animal_count_update', {'count': count_var})
    socketio.emit('detections_update', {'detections': csv_str})
    socketio.emit('threat_update', {'threat': threat_type})
    print('emitted updates from app.py')


# farm route
@app.route("/farm", methods = ['GET', 'POST'])
def farm():
    if request.method == 'POST':
        
        if (request.form['video_source'] == ''):
            inval_feed ="No Video-Found"
            return render_template('farm.html', var2 = inval_feed)
        
        else:
            video_source = request.form['video_source']
            vd_feed = "Video-Feed"
            return render_template('farm.html', video_source = video_source, var2 = vd_feed)
    
    if request.method == 'GET':
        return render_template('farm.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)