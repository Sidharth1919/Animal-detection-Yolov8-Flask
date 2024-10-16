# importing libraries
from flask import Flask, render_template, Response, request
from flask_login import login_required, current_user
from flask_socketio import SocketIO
from bson import ObjectId
import os
import signal
import cv2
from ultralytics import YOLO
import numpy as np
from auth import app, login_manager, mongo, auth_bp
from auth import login, signup, logout
import os
from datetime import datetime

# global variables
count_var = 0 # variable to store the count of animals
threat_type = "None" 
detection_list = [] # list to store the detected classes
csv_str = "none"
class_index = -1


# creating flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '1010'

login_manager.init_app(app)
socketio = SocketIO(app)
app.register_blueprint(auth_bp)


# home route
@app.route("/")
@login_required
def index():
    return render_template('index.html')

# socketio event for updating the class from home page option
@socketio.on('update_class_index')
def handle_update_class_index(json):
    global class_index
    class_index = json.get('classIndex')
    user_id = current_user.id  # Assuming current_user is available

    if ObjectId.is_valid(user_id):
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'selected_farm_animal': int(class_index)}}
        )

    print('received class index: ' + str(class_index))
    

VIDEO_FILE_PATH = None

@socketio.on('video_file_selected')
def handle_video_file_selected(video_file_name):
    global VIDEO_FILE_PATH 
    video_file_path = os.path.join('static/uploads/', video_file_name)
    VIDEO_FILE_PATH = video_file_path
    cap = cv2.VideoCapture(VIDEO_FILE_PATH)


def generate_frames(input_source, user_id):

    # access the global variable
    global count_var
    global threat_type
    global detection_list
    global csv_str
    global class_index
    model = YOLO("yolov8n.pt")

    if input_source == 0:  # Webcam
        cap = cv2.VideoCapture(0)
    elif input_source == 1:  # cam
        cap = cv2.VideoCapture('http://url:port/video')
    elif input_source == 2:  # Video file
        cap = cv2.VideoCapture(VIDEO_FILE_PATH)
    elif input_source not in [0, 1, 2]:  # Validate input source
        return "Invalid video source, please enter 0, 1, or 2"
    
    if not cap.isOpened():
        print("Error opening video stream or file")
        return "Error opening video stream or file. Please check the source or file integrity."
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
        # print("results: ",results)
        result = results[0]
        # print("result: ",result)

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

# ---------------------------------------------------------------------------------------

        try:
            if user_id is not None and ObjectId.is_valid(user_id):
                timestamp = datetime.now()
                
                for i in range(len(classes)):
                    detected_class = names[classes[i]]
                    detection = {
                        "timestamp": timestamp,
                        "detected_class": detected_class,
                        "count": count_var  # Add the count
                    }
                    user_collection = mongo.db[f"user_{user_id}"]

                    user_collection.update_one(
                        {"user_id": ObjectId(user_id), "farm_index": int(class_index), "video_source": input_source},
                        {"$push": {"detections": detection}},
                        upsert=True
                    )

                for threat in threat_types:
                    threat_data = {
                        "timestamp": timestamp,
                        "threat_type": threat
                    }
                    user_collection = mongo.db[f"user_{user_id}"]

                    user_collection.update_one(
                        {"user_id": ObjectId(user_id), "farm_index": int(class_index), "video_source": input_source},
                        {"$push": {"threats": threat_data}},
                        upsert=True
                    )
            else:
                print("User ID is None or invalid")
                continue
        except Exception as e:
            print(f"Error occurred in generate_frames: {e}")
            continue

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
    user_id = str(current_user.id)
    print('user_id:', user_id)

    return Response(generate_frames(video_source, user_id), mimetype='multipart/x-mixed-replace; boundary=frame')


@socketio.on('send_updates')
def emit_updates():
    global count_var, csv_str, threat_type
    socketio.emit('animal_count_update', {'count': count_var})
    socketio.emit('detections_update', {'detections': csv_str})
    socketio.emit('threat_update', {'threat': threat_type})
    print('emitted updates from app.py')


# farm route
@app.route("/farm", methods = ['GET', 'POST'])
@login_required
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
    
@app.route('/dashboard/<user_id>')
@login_required
def dashboard(user_id):
    user_collection = mongo.db[f"user_{user_id}"]
    farm_data = {}

    # Cow Farm (index 19)
    cow_farm_data = user_collection.find_one({"farm_index": 19})
    if cow_farm_data:
        farm_data["Cow Farm"] = process_farm_data(cow_farm_data)

    # Sheep Farm (index 18)
    sheep_farm_data = user_collection.find_one({"farm_index": 18})
    if sheep_farm_data:
        farm_data["Sheep Farm"] = process_farm_data(sheep_farm_data)

    # Horse Farm (index 17)
    horse_farm_data = user_collection.find_one({"farm_index": 17})
    if horse_farm_data:
        farm_data["Horse Farm"] = process_farm_data(horse_farm_data)

    if not farm_data:
        return render_template('dashboard.html', error='No data available for the user.')

    return render_template('dashboard.html', farm_data=farm_data, error=None)

def process_farm_data(farm_data):
    # Prepare the data for the tables
    detections = farm_data.get('detections', [])
    video_source_counts = farm_data.get('video_source_counts', {})
    threats = farm_data.get('threats', [])

    # Animal Detection Data
    animal_detection_data = {}
    for detection in detections:
        animal_type = detection['detected_class']
        count = detection['count']
        animal_detection_data[animal_type] = animal_detection_data.get(animal_type, 0) + count

    # Animal Count Over Time Data
    animal_count_data = [
        {'timestamp': detection['timestamp'], 'detections': detection['detected_class'], 'count': detection['count']}
        for detection in detections
    ]

    # Threat Detection Data
    threat_detection_data = [
        {'timestamp': threat['timestamp'], 'threat_type': threat['threat_type']}
        for threat in threats
    ]

    # Video Source Data
    video_source_data = video_source_counts

    # Summary Statistics
    if animal_detection_data:  # Check if animal_detection_data is not empty
        animal_counts = animal_detection_data.values()
        total_animals = sum(animal_counts)
        most_common_animal = max(animal_detection_data, key=animal_detection_data.get)
    else:
        total_animals = 0
        most_common_animal = "None"

    most_common_threat = max((threat['threat_type'] for threat in threat_detection_data), key=(
        lambda x: sum(1 for t in threat_detection_data if t['threat_type'] == x)), default='None')

    return {
        'animal_detection_data': animal_detection_data,
        'animal_count_data': animal_count_data,
        'threat_detection_data': threat_detection_data,
        'video_source_data': video_source_data,
        'total_animals': total_animals,
        'most_common_animal': most_common_animal,
        'most_common_threat': most_common_threat
    }

if __name__ == '__main__':
    socketio.run(app, debug=True)
