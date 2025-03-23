import sys
import pandas as pd
import os
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QInputDialog, QFormLayout, QLineEdit
)
from PyQt5.QtGui import QFont

# Define paths
ATTENDANCE_FILE = os.path.join("attendance_logs", "attendance.csv")
DATASET_DIR = "dataset"

# Ensure dataset directory exists
os.makedirs(DATASET_DIR, exist_ok=True)

class AdminPage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Admin Panel")
        self.setGeometry(200, 200, 800, 500)

        layout = QVBoxLayout()
        
        self.label = QLabel("Attendance Records", self)
        self.label.setFont(QFont("Arial", 14))
        layout.addWidget(self.label)

        self.table = QTableWidget(self)
        self.load_attendance_data()
        layout.addWidget(self.table)

        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.setFont(QFont("Arial", 12))
        self.refresh_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        self.refresh_button.clicked.connect(self.load_attendance_data)
        layout.addWidget(self.refresh_button)

        self.register_button = QPushButton("Register Face", self)
        self.register_button.setFont(QFont("Arial", 12))
        self.register_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
        self.register_button.clicked.connect(self.register_face)
        layout.addWidget(self.register_button)

        self.delete_button = QPushButton("Delete Selected", self)
        self.delete_button.setFont(QFont("Arial", 12))
        self.delete_button.setStyleSheet("background-color: #d9534f; color: white; padding: 10px; border-radius: 5px;")
        self.delete_button.clicked.connect(self.delete_selected)
        layout.addWidget(self.delete_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.setFont(QFont("Arial", 12))
        self.close_button.setStyleSheet("background-color: #d9534f; color: white; padding: 10px; border-radius: 5px;")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def load_attendance_data(self):
        """Load and display attendance data from the CSV file."""
        if not os.path.exists(ATTENDANCE_FILE):
            QMessageBox.warning(self, "Error", "Attendance file not found!")
            return

        df = pd.read_csv(ATTENDANCE_FILE)

        # Calculate attendance percentage for each person
        df["Attendance Percentage"] = (df["Days Present"] / (df["Days Present"] + df["Days Absent"])) * 100
        df["Attendance Percentage"] = df["Attendance Percentage"].round(2)  # Round to 2 decimal places

        # Update the table
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                self.table.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

    def register_face(self):
        """Register a new face by capturing an image and saving it to the dataset."""
        # Create a form to collect details
        form = QWidget()
        form.setWindowTitle("Registration Form")
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.roll_no_input = QLineEdit()
        self.branch_input = QLineEdit()
        self.mobile_no_input = QLineEdit()

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Roll No:", self.roll_no_input)
        form_layout.addRow("Branch:", self.branch_input)
        form_layout.addRow("Mobile No:", self.mobile_no_input)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(lambda: self.capture_face(form))
        form_layout.addRow(submit_button)

        form.setLayout(form_layout)
        form.show()

    def capture_face(self, form):
        """Capture the face after collecting details."""
        name = self.name_input.text().strip()
        roll_no = self.roll_no_input.text().strip()
        branch = self.branch_input.text().strip()
        mobile_no = self.mobile_no_input.text().strip()

        if not name or not roll_no or not branch or not mobile_no:
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        # Open the camera to capture an image
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.critical(self, "Error", "Failed to open the camera! Please check if the camera is connected and accessible.")
            return

        # Keep the camera open until the user presses a key
        while True:
            ret, frame = cap.read()
            if not ret:
                QMessageBox.critical(self, "Error", "Failed to capture image! Please check the camera.")
                cap.release()
                return

            # Display the live camera feed
            cv2.imshow("Press 'Enter' to Capture, 'Esc' to Cancel", frame)

            # Wait for a key press
            key = cv2.waitKey(1) & 0xFF

            # If 'Enter' is pressed, capture the image
            if key == 13:  # 13 is the ASCII code for Enter
                # Save the captured image to the dataset directory
                image_path = os.path.join(DATASET_DIR, f"{name}.jpg")
                try:
                    success = cv2.imwrite(image_path, frame)
                    if success:
                        # Save the details to the attendance file
                        self.save_details(name, roll_no, branch, mobile_no)
                        QMessageBox.information(self, "Success", f"Face registered for: {name}")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to save the image! Check if the dataset directory is accessible.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save the image: {str(e)}")
                break

            # If 'Esc' is pressed, cancel the operation
            elif key == 27:  # 27 is the ASCII code for Esc
                QMessageBox.information(self, "Cancelled", "Face registration cancelled.")
                break

        # Release the camera and close the OpenCV window
        cap.release()
        cv2.destroyAllWindows()
        form.close()

    def save_details(self, name, roll_no, branch, mobile_no):
        """Save the registration details to the attendance file."""
        if not os.path.exists(ATTENDANCE_FILE):
            df = pd.DataFrame(columns=["Name", "Roll No", "Branch", "Mobile No", "Days Present", "Days Absent", "Absent Dates","Attendance Percentage"])
        else:
            df = pd.read_csv(ATTENDANCE_FILE)

        # Check if the name already exists
        if name in df["Name"].values:
            QMessageBox.warning(self, "Error", f"{name} is already registered!")
            return

        # Add the new entry
        df = pd.concat([df, pd.DataFrame([[
            name, roll_no, branch, mobile_no, 0, 0, "",0
        ]], columns=df.columns)], ignore_index=True)

        # Save the updated dataframe
        df.to_csv(ATTENDANCE_FILE, index=False)

    def delete_selected(self):
        """Delete the selected person's data from the attendance file and their image from the dataset."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "No row selected! Please select a row to delete.")
            return

        # Get the name of the selected person
        name_item = self.table.item(selected_row, 0)  # Assuming the name is in the first column
        if not name_item:
            QMessageBox.warning(self, "Error", "No name found in the selected row!")
            return

        name = name_item.text()

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete all data for {name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.No:
            return

        # Delete the person's image from the dataset
        image_path = os.path.join(DATASET_DIR, f"{name}.jpg")
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete image: {str(e)}")
                return

        # Delete the person's data from the attendance file
        if not os.path.exists(ATTENDANCE_FILE):
            QMessageBox.warning(self, "Error", "Attendance file not found!")
            return

        df = pd.read_csv(ATTENDANCE_FILE)
        df = df[df["Name"] != name]  # Remove the row with the selected name
        df.to_csv(ATTENDANCE_FILE, index=False)

        # Refresh the table
        self.load_attendance_data()
        QMessageBox.information(self, "Success", f"Data for {name} has been deleted.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminPage()
    window.show()
    sys.exit(app.exec_())