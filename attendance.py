import sys
import cv2
import face_recognition
import numpy as np
import os
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox, QInputDialog, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QLineEdit

# Define directories
DATASET_DIR = 'dataset'
CAPTURED_IMAGES_DIR = 'captured_images'
ATTENDANCE_DIR = 'attendance_logs'
ATTENDANCE_FILE = os.path.join(ATTENDANCE_DIR, 'attendance.csv')

# Ensure necessary directories exist
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(CAPTURED_IMAGES_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# Load known faces
def load_known_faces():
    known_face_encodings = []
    known_face_names = []

    for image_file in os.listdir(DATASET_DIR):
        image_path = os.path.join(DATASET_DIR, image_file)
        image = face_recognition.load_image_file(image_path)

        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(image_file)[0])

    return known_face_encodings, known_face_names

# Log attendance
def log_attendance(name):
    today = datetime.now().strftime('%Y-%m-%d')

    # Check if the attendance file exists
    if not os.path.exists(ATTENDANCE_FILE):
        # Create a new DataFrame with the required columns
        df = pd.DataFrame(columns=["Name", "Roll No", "Branch", "Mobile No", "Date", "Days Present", "Days Absent", "Absent Dates"])
    else:
        # Load the existing CSV file
        df = pd.read_csv(ATTENDANCE_FILE)

    # Check if the name already exists in the DataFrame
    if name in df["Name"].values:
        user_row = df[df["Name"] == name]
        if today in user_row["Date"].values:
            QMessageBox.information(None, "Attendance", "Attendance for today is already marked.")
            return

        # Update the existing user's attendance
        df.loc[df["Name"] == name, "Days Present"] += 1
        df.loc[df["Name"] == name, "Date"] = today
    else:
        # Add a new entry for the user
        new_entry = {
            "Name": name,
            "Roll No": "",  # Default value for Roll No
            "Branch": "",   # Default value for Branch
            "Mobile No": "",  # Default value for Mobile No
            "Date": today,
            "Days Present": 1,
            "Days Absent": 0,
            "Absent Dates": ""
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

    # Save the updated DataFrame to the CSV file
    df.to_csv(ATTENDANCE_FILE, index=False)

class FaceRecognitionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.known_face_encodings, self.known_face_names = load_known_faces()
        self.video_capture = cv2.VideoCapture(0)
        
        if not self.video_capture.isOpened():
            QMessageBox.critical(self, "Camera Error", "Failed to open the camera!")
            sys.exit(1)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
    
    def initUI(self):
        self.setWindowTitle('Face Recognition Attendance')
        self.setGeometry(100, 100, 1200, 700)  # Increased width to accommodate the right panel
        self.setStyleSheet("background-color: #f4f4f4;")

        # Main layout
        main_layout = QHBoxLayout()

        # Left panel (video and buttons)
        left_panel = QVBoxLayout()

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.video_label)

        self.status_label = QLabel('Status: Waiting...', self)
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #333;")
        left_panel.addWidget(self.status_label)

        # Capture Face Button
        self.capture_button = QPushButton('Capture Face', self)
        self.capture_button.setFont(QFont("Arial", 10))  # Smaller font size
        self.capture_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                border: 1px solid #45a049;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.capture_button.setIcon(QIcon("icons/capture.png"))
        self.capture_button.setFixedSize(150, 40)  # Set fixed size
        left_panel.addWidget(self.capture_button)

        # Admin Login Button
        self.admin_button = QPushButton('Admin Login', self)
        self.admin_button.setFont(QFont("Arial", 10))  # Smaller font size
        self.admin_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                border: 1px solid #e68a00;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            """
        )
        self.admin_button.setIcon(QIcon("icons/admin.png"))
        self.admin_button.setFixedSize(150, 40)  # Set fixed size
        left_panel.addWidget(self.admin_button)

        # Quit Button
        self.quit_button = QPushButton('Quit', self)
        self.quit_button.setFont(QFont("Arial", 10))  # Smaller font size
        self.quit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #d9534f;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                border: 1px solid #c9302c;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            """
        )
        self.quit_button.setIcon(QIcon("icons/exit.png"))
        self.quit_button.setFixedSize(150, 40)  # Set fixed size
        left_panel.addWidget(self.quit_button)

        # Right panel (total attendance)
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignTop)

        self.total_attendance_label = QLabel('Total Attendance: 0', self)
        self.total_attendance_label.setFont(QFont("Arial", 14))
        self.total_attendance_label.setStyleSheet("color: #333;")
        right_panel.addWidget(self.total_attendance_label)

        # Add left and right panels to the main layout
        main_layout.addLayout(left_panel, 70)  # 70% width for left panel
        main_layout.addLayout(right_panel, 30)  # 30% width for right panel

        self.setLayout(main_layout)

        # Connect buttons to functions
        self.capture_button.clicked.connect(self.capture_face)
        self.quit_button.clicked.connect(self.close)
        self.admin_button.clicked.connect(self.admin_login)

        # Update total attendance initially
        self.update_total_attendance()
    
    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            step = channel * width
            qImg = QImage(frame.data, width, height, step, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qImg))
    
    def capture_face(self):
        ret, frame = self.video_capture.read()
        if not ret:
            self.status_label.setText("Error: Failed to capture frame")
            return
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(image)
        
        if not face_encodings:
            self.status_label.setText("No face detected!")
            return
        
        name = "Unknown"
        matches = face_recognition.compare_faces(self.known_face_encodings, face_encodings[0], tolerance=0.6)
        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encodings[0])
        best_match_index = np.argmin(face_distances) if face_distances.size > 0 else None
        
        if best_match_index is not None and matches[best_match_index]:
            name = self.known_face_names[best_match_index]
            log_attendance(name)
            attendance_percentage = self.calculate_attendance_percentage(name)
            self.status_label.setText(f"Attendance Marked for: {name}\nAttendance Percentage: {attendance_percentage:.2f}%")
            self.update_total_attendance()  # Update total attendance
        else:
            self.status_label.setText("Face not recognized!")

    def calculate_attendance_percentage(self, name):
        """Calculate the attendance percentage for a given person."""
        if not os.path.exists(ATTENDANCE_FILE):
            return 0.0

        df = pd.read_csv(ATTENDANCE_FILE)
        user_row = df[df["Name"] == name]

        if user_row.empty:
            return 0.0

        days_present = user_row["Days Present"].values[0]
        days_absent = user_row["Days Absent"].values[0]
        total_days = days_present + days_absent

        if total_days == 0:
            return 0.0

        return (days_present / total_days) * 100

    def update_total_attendance(self):
        """Update the total attendance count."""
        if not os.path.exists(ATTENDANCE_FILE):
            self.total_attendance_label.setText("Total Attendance: 0")
            return

        df = pd.read_csv(ATTENDANCE_FILE)
        total_attendance = df["Days Present"].sum()
        self.total_attendance_label.setText(f"Total Attendance: {total_attendance}")

    def admin_login(self):
        user_id, ok1 = QInputDialog.getText(self, "Admin Login", "Enter User ID:")
        password, ok2 = QInputDialog.getText(self, "Admin Login", "Enter Password:", QLineEdit.EchoMode.Password)
        if ok1 and ok2 and user_id == "ruhi" and password == "ruhi":
            QMessageBox.information(self, "Login Successful", "Welcome, Admin!")
            self.open_admin_page()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid credentials!")

    def open_admin_page(self):
        os.system("python admin_page.py")  # Open the admin panel

    def closeEvent(self, event):
        self.video_capture.release()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    window.show()
    sys.exit(app.exec_())