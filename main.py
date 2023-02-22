import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from QRIn import QRCodeScannerIn
from QROut import QRCodeScannerOut


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.qr_code_scanner = None
        self.setWindowTitle("QR Code Scanner")

        dark_stylesheet = """
            QWidget {
                background-color: #303030;
                color: #EAEAEA;
            }

            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border-radius: 20px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #424242;
            }

            QPushButton:pressed {
                background-color: #1e1e1e;
            }

            QLabel {
                color: #EAEAEA;
            }

            QStatusBar {
                background-color: #3C3F41;
                color: #EAEAEA;
            }
        """

        self.setStyleSheet(dark_stylesheet)

        # Create the ulaz and izlaz buttons
        self.ulaz_button = QPushButton("Ulaz")
        self.izlaz_button = QPushButton("Izlaz")

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.ulaz_button)
        layout.addWidget(self.izlaz_button)

        # Set the layout to the main window
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connect the ulaz and izlaz buttons to their respective functions
        self.ulaz_button.clicked.connect(self.ulaz)
        self.izlaz_button.clicked.connect(self.izlaz)

    def ulaz(self):
        self.qr_code_scanner = QRCodeScannerIn()
        self.qr_code_scanner.showFullScreen()

    def izlaz(self):
        self.qr_code_scanner = QRCodeScannerOut()
        self.qr_code_scanner.showFullScreen()


    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())
