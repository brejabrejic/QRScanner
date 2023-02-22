import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from QRIn import QRCodeScanner


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Scanner")

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
        self.qr_code_scanner = QRCodeScanner("ULAZ")
        self.qr_code_scanner.showFullScreen()

    def izlaz(self):
        self.qr_code_scanner = QRCodeScanner("IZLAZ")
        self.qr_code_scanner.showFullScreen()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())
