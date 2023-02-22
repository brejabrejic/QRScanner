import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt
from QRIn import QRCodeScannerIn
from QROut import QRCodeScannerOut


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.qr_code_scanner = None

        # Setting the window title to QR Code Scanner
        self.setWindowTitle("QR Code Scanner")

        # Open config.json, find the dark_stylesheet in the data and then close the file
        f = open('cfg/config.json', 'r')
        json_data = json.loads(f.read())
        self.setStyleSheet(json_data['dark_stylesheet'])
        f.close()

        # Create ulaz button
        self.ulaz_button = QPushButton("Ulaz")
        # setSizePolicy sets the size policy of the button. QSizePolicy.Expanding makes it Expand
        self.ulaz_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create izlaz button
        self.izlaz_button = QPushButton("Izlaz")
        # setSizePolicy sets the size policy of the button. QSizePolicy.Expanding makes it Expand
        self.izlaz_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # Set up the layout
        layout = QVBoxLayout()

        # Add ulaz_button and izlaz_button to the layout
        layout.addWidget(self.ulaz_button)
        layout.addWidget(self.izlaz_button)

        # Initiate a QWidget and set the widget layout to the layout we created.
        widget = QWidget()
        widget.setLayout(layout)
        # Set our widget as the central widget
        self.setCentralWidget(widget)

        # Connect the ulaz button to their respective functions
        self.ulaz_button.clicked.connect(self.ulaz)

        # Connect the izlaz button to their respective functions
        self.izlaz_button.clicked.connect(self.izlaz)

    # Ulaz button method
    def ulaz(self):
        # qr_code_scanner is calling the class QRCodeScannerIn that's used to scan check ins
        self.qr_code_scanner = QRCodeScannerIn()
        # The window is fullscreen
        self.qr_code_scanner.showFullScreen()

    # Izlaz button method
    def izlaz(self):
        # qr_code_scanner is calling the class QRCodeScannerOut that's used to scan for check outs
        self.qr_code_scanner = QRCodeScannerOut()
        self.qr_code_scanner.showFullScreen()

    # Keypress event - Escape closes the program
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())
