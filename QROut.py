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
from pymongo.errors import ConnectionFailure


class QRCodeScannerOut(QMainWindow):
    def __init__(self):
        super().__init__()
        self.check_connection_timer = None
        self.setWindowTitle("QR Code Scanner")
        self.label = QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(self.label)

        # Set scaledContents property to True
        self.label.setScaledContents(True)

        try:
            self.db_client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
            self.statusBar().showMessage("Connected to database.")
        except ConnectionFailure:
            self.db_client = None
            self.statusBar().showMessage("Connection to database failed.")
            self.error_message = QMessageBox()
            self.error_message.setText('No connection to the database.')
            self.error_message.setWindowTitle('Error')
            self.error_message.show()
            self.close()
            return

        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

        self.setStyleSheet('''background-color:grey''')
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.error_message = None
        self.success_message = None
        self.scanned = False
        self.statusBar().showMessage("Connecting to database...")

    def check_connection(self):
        try:
            if self.db_client is None:
                raise ConnectionFailure('Connection to database not established')
            # Connection to database established, update status message
            self.statusBar().showMessage("Connected to database.")
        except ConnectionFailure:
            print('Error: Connection to database not established')
            self.timer.stop()
            self.check_connection_timer.stop()
            self.db_client = None  # Set db_client to None when the check fails
            self.error_message = QMessageBox()
            self.error_message.setText('No connection to server.')
            self.error_message.setWindowTitle('Error')
            self.error_message.show()
            self.close()

    def update_frame(self):
        if self.db_client is None:
            self.check_connection()

        ret, frame = self.camera.read()
        if not ret:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        decoded_objs = decode(frame)

        for obj in decoded_objs:
            data = obj.data.decode('utf-8')

            try:
                # Find the corresponding MongoDB document using the _id
                document = self.db_client['Upravljanje_Banja_Luka']['Radnici'].find_one({"_id": ObjectId(data)})

                if document and not self.scanned:
                    self.scanned = True
                    self.camera.release()
                    self.timer.stop()
                    # Add datetime stamp to image
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    bottom_left_corner = (10, frame.shape[0] - 10)
                    font_scale = 0.5
                    font_color = (255, 0, 0)
                    line_type = 1
                    cv2.putText(frame, str(document['Prezime']) + ' ' + str(document['Ime'])
                                + ' - '
                                + datetime.now().strftime('%d.%m.%Y, %H:%M:%S'),
                                bottom_left_corner,
                                font, font_scale, font_color, line_type)

                    # Save image to file
                    filename = '{}_{}.png'.format(data, datetime.now().strftime('%d%m%Y(_%H%M%S'))
                    filepath = os.path.join('IZLAZ', filename)
                    frame[:, :, [0, 2]] = frame[:, :, [2, 0]]
                    cv2.imwrite(filepath, frame)
                    self.close()

                    # Display success message and close it after 1 second
                    self.success_message = QMessageBox()

                    self.success_message.setText('Prijavljen izlaz {} {}!'.format(
                                                str(document['Prezime']), str(document['Ime'])))
                    self.success_message.setStandardButtons(QMessageBox.NoButton)  # Remove the Ok button
                    self.success_message.setWindowTitle('Prijava')
                    self.success_message.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                    self.success_message.setStyleSheet('QLabel{'
                                                       'qproperty-alignment: AlignCenter; '
                                                       'font-size: 13pt; color: white;} \
                                                       QMessageBox{background-color: black; '
                                                       '}')
                    self.success_message.show()

                    QtCore.QTimer.singleShot(1000, self.success_message.accept)

                points = obj.polygon
                if len(points) > 4:
                    hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                    hull = list(map(tuple, np.squeeze(hull)))
                else:
                    hull = points

                n = len(hull)
                for j in range(0, n):
                    cv2.line(frame, hull[j], hull[(j + 1) % n], (255, 0, 0), 3)

            except:
                points = obj.polygon
                if len(points) > 4:
                    hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                    hull = list(map(tuple, np.squeeze(hull)))
                else:
                    hull = points

                n = len(hull)
                for j in range(0, n):
                    cv2.line(frame, hull[j], hull[(j + 1) % n], (255, 0, 0), 1)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    bottom_left_corner = (points[0][0], points[0][1] - 5)
                    font_scale = 0.5
                    font_color = (255, 0, 0)
                    line_type = 1
                    cv2.putText(frame, 'Ne postoji', bottom_left_corner, font, font_scale, font_color, line_type)


        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)

        q_pixmap = QtGui.QPixmap.fromImage(q_img)
        self.label.setPixmap(q_pixmap)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.camera.release()
            self.timer.stop()
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QRCodeScannerOut()
    window.showFullScreen()
    sys.exit(app.exec_())
