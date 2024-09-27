import asyncio
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QSize
from .guilogger import GUILogger


class AcquisitionUI(QWidget):
    def __init__(self, main, parent):
        super().__init__(parent)
        main.setWindowTitle("IMU Data Acquisition")
        font = QFont('Arial', 12)                               # Default font

        # Create a main layout
        main_layout = QVBoxLayout()
        parent.setLayout(main_layout)
        
        # Create a layout for all input and plot options
        top_layout = QHBoxLayout()
        
        # Create a layout for main control options
        top_layout = QVBoxLayout()
            
        # Create data path field and browse button
        path_layout = QHBoxLayout()

        # Create data path input field
        main.imu_path_input = QLineEdit(parent)
        main.imu_path_input.setPlaceholderText("Data path (default: ./output)")  # Placeholder text
        main.imu_path_input.setFixedSize(355, 40)
        path_layout.addWidget(main.imu_path_input)

        # Create a button with a folder icon
        main.imu_browse_button = QToolButton(parent)
        main.imu_browse_button.setIcon(
            main.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        )
        main.imu_browse_button.setIconSize(QSize(30, 30))
        main.imu_browse_button.setFixedSize(40, 40)
        path_layout.addWidget(main.imu_browse_button)

        top_layout.addLayout(path_layout)

        # Create the "Scan" button
        main.scan_button = QPushButton(" Device Scan", parent)
        main.scan_button.setIcon(
            main.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        )
        main.scan_button.setFixedSize(400, 40)
        main.scan_button.setFont(font)
        top_layout.addWidget(main.scan_button)

        # Add a label for scanned devices
        main.scanned_devices_label = QLabel("Motion Trackers:", parent)
        main.scanned_devices_label.setFont(font)
        top_layout.addWidget(main.scanned_devices_label)
        
        # Add devices and checkboxes within a QFrame
        main.device_frame = QFrame(parent)
        main.device_frame.setFrameShape(QFrame.Shape.Box)
        main.device_frame.setFixedSize(400, 200)
        main.device_frame_layout = QVBoxLayout()
        main.device_frame.setLayout(main.device_frame_layout)
        top_layout.addWidget(main.device_frame)
        
        # Create acquisition control layout
        acquisition_layout = QHBoxLayout()

        # Create the "Start" button
        main.start_button = QPushButton(" Start", parent)
        main.start_button.setIcon(
            main.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        main.start_button.setFixedSize(197, 40)
        main.start_button.setFont(font)
        main.start_button.setEnabled(False)
        acquisition_layout.addWidget(main.start_button)

        # Create the "Stop" button
        main.stop_button = QPushButton(" Stop", parent)
        main.stop_button.setIcon(
            main.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        )
        main.stop_button.setFixedSize(197, 40)
        main.stop_button.setFont(font)
        main.stop_button.setEnabled(False)
        acquisition_layout.addWidget(main.stop_button)

        top_layout.addLayout(acquisition_layout)
        
        # Create a layout for the log output
        bottom_layout = QVBoxLayout()
        
        # Create a log output field
        main.log_output = GUILogger(parent)
        main.log_output.widget.setStyleSheet("border: 1px solid gray;")
        main.log_output.widget.setMinimumHeight(170)
        bottom_layout.addWidget(main.log_output.widget)
        
        # Add layouts to main layout
        main_layout.addLayout(top_layout,1)
        main_layout.addLayout(bottom_layout,2)
        
        # Connect button actions to related methods to be activated on release
        main.imu_browse_button.clicked.connect(main.browse_imu_path)
        main.scan_button.clicked.connect(lambda: asyncio.ensure_future(main.scan_for_devices()))
        main.start_button.clicked.connect(lambda: asyncio.ensure_future(main.start_recording()))
        main.stop_button.clicked.connect(lambda: asyncio.ensure_future(main.stop_recording()))
