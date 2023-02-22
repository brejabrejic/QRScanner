import json
import cv2
import sys
import numpy as np
import os
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox
from bson import ObjectId
from pyzbar.pyzbar import decode
from datetime import datetime
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson.errors import InvalidId


class QRCodeScannerIn(QMainWindow):
    def __init__(self):
        super().__init__()
        self.check_connection_timer = None
        # Set window title
        self.setWindowTitle("QR Code Scanner")
        # Label that we will be using for the pixmap
        self.label = QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        # Set the label as the central widget
        self.setCentralWidget(self.label)

        # Set scaledContents property to True - Scales the label to fit the screen
        self.label.setScaledContents(True)
        self.statusBar().showMessage("Connecting to database...")
        try:
            # Open Config file
            f = open('cfg/config.json', "r")
            # Get json data
            json_data = json.loads(f.read())

            # self.db_client is a instance of a pymongo-MongoClient connection.
            # json_data['host'] contains the host string
            self.db_client = pymongo.MongoClient(json_data['host'], serverSelectionTimeoutMS=1500)
            # Status bar shows the message Connected to Database if there's a connection established
            self.statusBar().showMessage("Cekam scan za QR Code....")

            # close the json file that we opened earlier at the top of the try block
            f.close()

        # Except block - ConnectionFailure
        except ConnectionFailure:
            # If the Connection fails our self.db_client is equal to None
            self.db_client = None
            # Status bar shows message that the Connection to the database failed
            self.statusBar().showMessage("Nema veze sa serverom....")
            return

        # self.camera initiates the cv2 videocapture. cv2.CAP_DSHOW makes the camera open faster for some reason
        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # Initiate timer
        self.timer = QtCore.QTimer(self)

        # Connect the timer to the method update_frame
        self.timer.timeout.connect(self.update_frame)
        # Start the timer every 3 miliseconds
        self.timer.start(3)

        # Make background color of the window grey
        self.setStyleSheet('''background-color:grey''')

        self.error_message = None
        self.success_message = None
        self.scanned = False

    # Update frame method
    def update_frame(self):
        # ret - boolean value representing if the frame was read or not - True or False
        # frame - video frame
        ret, frame = self.camera.read()

        # If ret returns False return
        if not ret:
            return

        # converts the frame from the BGR color space to the RGB (red-green-blue) color space,\
        # which is the format that PyQt5 expects for displaying images.
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # decoded_objs is a variable used to store the data that are being decoded from the frame
        # decode is a function provided by pyzbar
        decoded_objs = decode(frame)

        # decoded_objs are returned as a list of objects so we need to go through the list
        for obj in decoded_objs:
            # decode the data into utf-8
            data = obj.data.decode('utf-8')

            # Try block
            try:
                # Find the corresponding MongoDB document using the _id
                document = self.db_client['Upravljanje_Banja_Luka']['Radnici'].find_one({"_id": ObjectId(data)})

                # check whether the variable document is not None or False, and whether self.scanned is False
                if document and not self.scanned:
                    # the document is not None now and self.scanned is now True
                    self.scanned = True
                    # stop the camera
                    self.camera.release()
                    # stop the timer
                    self.timer.stop()

                    # Add stamp to image
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    bottom_left_corner = (10, frame.shape[0] - 10)
                    font_scale = 0.5
                    font_color = (255, 0, 0)
                    line_type = 1

                    # The stamp will contain the last name, first name and the current date and time
                    cv2.putText(frame, 'Ulaz - '+str(document['Prezime']) + ' ' + str(document['Ime'])
                                + ' - '
                                + datetime.now().strftime('%d.%m.%Y, %H:%M:%S'),
                                bottom_left_corner,
                                font, font_scale, font_color, line_type)

                    # Save image to file
                    # File name is formated to be named after the scanned data+current date and time
                    filename = '{}_{}.png'.format(data, datetime.now().strftime('%d.%m.%Y_%H%M%S'))

                    # The image goes to the folder ULAZ and then to a folder that fits its corresponding date.
                    # If the path doesn't exist we are making one with os
                    cwd = os.getcwd()
                    path = cwd+'\\ULAZ\\'+datetime.now().strftime('%d.%m.%Y')
                    existing_path_check = os.path.exists(path)
                    print(path)
                    # if path exists-pass
                    if existing_path_check is True:
                        pass
                    else:
                        # Else make the directory
                        os.makedirs(path)
                    # File actual path with the file name
                    filepath = os.path.join(path, filename)

                    # We are reversing the colors back to normal before writing the image.
                    # We don't need the PyQt reversed colors anymore
                    frame[:, :, [0, 2]] = frame[:, :, [2, 0]]

                    # Write the frame to an image and save it to the file path
                    cv2.imwrite(filepath, frame)
                    # Close the window
                    self.close()

                    # Since we have the document - that means we have established the connection to our db
                    # We are going to make an check in entry to our db so we could do some data analysis later on
                    ulaz_collection = self.db_client['Upravljanje_Banja_Luka']['Ulaz']

                    # Create dictionary containing the information that is needed for further analysis
                    ulaz_dictionary = {
                        'id_radnika': document['_id'],
                        'dt': datetime.now(),
                        'ime': document['Ime'],
                        'prezime': document['Prezime'],
                        'img_path': filepath,
                        'type': 'ulaz'
                    }

                    # Insert the dictionary to the collection Ulaz inside our db
                    ulaz_collection.insert_one(ulaz_dictionary)

                    # Display success message and close it after 1 second
                    self.success_message = QMessageBox()
                    self.success_message.setText('Prijavljen ulaz {} {}!'.format(
                                                str(document['Prezime']), str(document['Ime'])))
                    self.success_message.setStandardButtons(QMessageBox.NoButton)  # Remove the Ok button
                    self.success_message.setWindowTitle('Prijava')
                    self.success_message.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                    self.success_message.setStyleSheet('QLabel{'
                                                       'qproperty-alignment: AlignCenter; '
                                                       'font-size: 13pt; color: white;} \
                                                       QMessageBox{background-color: black; '
                                                       '}')
                    # Show message
                    self.success_message.show()

                    # Timer accepts the QMessageBox after 1 second
                    QtCore.QTimer.singleShot(1000, self.success_message.accept)

            # Handle InvalidId - when document is not in our database
            # Handle ServerSelectionTimeoutError - when there's no connection to our database server
            except(InvalidId, ServerSelectionTimeoutError) as e:
                # If the error is ServerSelectionTimeoutError
                if isinstance(e, ServerSelectionTimeoutError):
                    # Release the camera, stop the timer and close the window
                    self.camera.release()
                    self.timer.stop()
                    self.close()

                    # Write the error to the log.txt file
                    with open('log.txt', 'a+') as f:
                        f.writelines(str(datetime.now())+','+str(e)+'\n')

                    # Display error message and close it after 2.5 seconds
                    self.error_message = QMessageBox()
                    self.error_message.setText('Veza sa serverom nije uspostavljena!\nPokusaj ponovo kasnije.')
                    self.error_message.setStandardButtons(QMessageBox.NoButton)  # Remove the Ok button
                    self.error_message.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                    self.error_message.setStyleSheet('QLabel{'
                                                     'qproperty-alignment: AlignCenter; '
                                                     'font-size: 11pt; color: white;} \
                                                     QMessageBox{background-color: black; '
                                                     '}')
                    # Show Error message box
                    self.error_message.show()
                    # error message box accepts its self and the QMessageBox closes itself in 2.5 seconds
                    QtCore.QTimer.singleShot(2500, self.error_message.accept)
                else:
                    # If there is no matching QR Code we're drawing a red rectangle around the QR Code
                    # obj.polygon is a list of four corner points of the detected QR code.
                    # The code checks if there are more than four points, which means that there are some extra points
                    # detected along with the four corners. In this case, the code applies the cv2.convexHull() function
                    # to the set of points to find the smallest convex polygon that surrounds all the points. The result
                    # is stored in the hull variable.
                    points = obj.polygon
                    if len(points) > 4:
                        hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                        hull = list(map(tuple, np.squeeze(hull)))
                    else:
                        hull = points

                    n = len(hull)
                    for j in range(0, n):
                        # Draw the red rectangle
                        cv2.line(frame, hull[j], hull[(j + 1) % n], (255, 0, 0), 1)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        bottom_left_corner = (points[0][0], points[0][1] - 5)
                        font_scale = 0.5
                        font_color = (255, 0, 0)
                        line_type = 1
                        cv2.putText(frame, 'Ne postoji', bottom_left_corner, font, font_scale, font_color, line_type)

        # unpack the dimensions of the frame into three variables, height, width, and channel
        height, width, channel = frame.shape

        # calculates the number of bytes per line for the QImage. Since each pixel in an RGB image consists of three
        # color channels (red, green, and blue), the number of bytes per line is the width of the image times 3
        bytes_per_line = 3 * width


        # This creates a QImage object using the QImage constructor.
        # The frame.data attribute contains the image data, which is passed as the first argument.
        # The second and third arguments are the width and height of the image, and the fourth argument is the number of
        # bytes per line. The fifth argument specifies the format of the image data, which in this case is
        # QtGui.QImage.Format_RGB888, indicating that the image data consists of 8-bit red, green,
        # and blue color channels in that order.
        q_img = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)

        # QtGui.QPixmap.fromImage(q_img) creates a QPixmap object from the QImage object q_img
        q_pixmap = QtGui.QPixmap.fromImage(q_img)


        # set the pixmap of self.label to q_pixmap. self.label is a QLabel object that was created earlier in the code,
        # and it is set as the central widget of the main window. Setting the pixmap of self.label updates the displayed
        # image in the window.
        self.label.setPixmap(q_pixmap)

    # keyPressEvent method
    def keyPressEvent(self, e):
        # Press Esc to close the app properly.
        if e.key() == Qt.Key_Escape:
            # Release camera
            self.camera.release()
            # Stop the timer
            self.timer.stop()
            # Close window
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QRCodeScannerIn()
    window.showFullScreen()
    sys.exit(app.exec_())
