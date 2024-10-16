# Animal Monitoring and Threat Detection system

## About 

This web-based application monitors and detects animals on a farm using real-time video feeds. It harnesses the power of the YOLO (You Only Look Once) object detection model through the Ultralytics framework, combined with Flask for backend operations and Flask-SocketIO for real-time communication between the client and server. The system features user authentication, real-time updates on detected animals, and threat alerts, making it an essential tool for modern farm management.

### Key Features

- **User Authentication**: Secures access to the application.
- **Real-Time Video Feed Processing**: Employs the YOLOv8 model for instantaneous animal detection.
- **Web Interface**: Offers a user-friendly interface to display detected animals and threats.
- **Real-Time Updates**: Provides live updates to users via Flask-SocketIO.
- **Multiple Video Sources**: Supports a range of video input sources including webcams and IP cameras.

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Sidharth1919/animal-detection.git
cd [project-directory]
```
Replace [project-directory] with the name of the directory into which the project is cloned.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```
Activate the virtual environment:

- On Windows:
```bash
venv\Scripts\activate
```
- On Unix or MacOS:
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies
Install the required dependencies by running:

```bash
pip install -r requirements.txt
```
This command will install all necessary packages listed in requirements.txt, including Flask, Flask-SocketIO, Flask-Login, Flask-PyMongo, OpenCV-Python, Ultralytics, and NumPy.

### Step 4: Set Up the Database
The project uses MongoDB as its database. Ensure you have MongoDB installed and running on your local machine or have access to a MongoDB instance. You can download MongoDB using this link, [MongoDB database](https://www.mongodb.com/try/download/community)

- Update the MONGO_URI in auth.py to point to your MongoDB instance. By default, it points to mongodb://localhost:27017/farmdb.

### Step 5: Run the Application
With all dependencies installed and the database configured, you can now run the application:

```bash
python app.py
```
The command above starts the Flask server. Open your web browser and navigate to http://localhost:5000 to access the application.
## Configuration

Adjust the application settings in `app.py` and `auth.py` to match your system's configuration, including the `SECRET_KEY` and database URI.

## Usage

After installation, navigate to the `/signup` page to create an account. Log in to access the dashboard where you can select the video source for monitoring. The system will automatically detect animals and potential threats, updating the dashboard in real-time.

## Acknowledgments

- [YOLO (Ultralytics)](https://ultralytics.com/yolo) for the object detection model.
- [Flask](https://flask.palletsprojects.com/) and [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/) for the web framework and real-time communication.
- [MongoDB](https://www.mongodb.com/) for the database management system.
- Parts of this project were inspired by the [Number of People In A Room](https://github.com/Ramesh86-TurBo/Number-Of-People-In-A-Room) repository by [Ramesh86-TurBo](https://github.com/Ramesh86-TurBo), with significant modifications and enhancements made to develop a comprehensive animal monitoring and threat detection system.

