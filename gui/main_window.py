import asyncio
import logging
from collections import deque
from PySide6.QtGui import QFont
from PySide6.QtCore import QEvent, QThread, Slot
from PySide6.QtWidgets import (
    QApplication, 
    QCheckBox, 
    QFileDialog, 
    QHBoxLayout, 
    QMainWindow, 
    QMessageBox, 
    QWidget, 
)

from gui import AcquisitionUI, ConnectionIndicator
import library as imu


class MainWindow(QMainWindow):
    """
    This is the main window class for the application. It contains the main UI elements and the logic to handle
    control and data streaming.
    """
    
    def __init__(self):
        super().__init__()
        
        # Read the configs
        self.imu_config = imu.conf
        
        # Set up tabs for the UI
        self.main_widget = QWidget()
        AcquisitionUI(self, self.main_widget)
        self.setCentralWidget(self.main_widget)
        
        # Set up logging
        self.imu_config = imu.conf
        self.log = imu.Log(log_file='log.txt', 
                       log_level=logging.DEBUG, 
                       gui_logger=self.log_output)
        self.log.info("Application started")

        # Set local variable defaults
        self.halt_event = asyncio.Event()
        self.checkboxes = []
        self.indicators = []
        self.imu_data_queues = {}

        # Set up a BT scanner for the motion trackers
        self.imu_scanner = imu.Scanner(self.imu_config, self.halt_event)
        self.imu_path = self.imu_config.output_folder

        # Set up data streaming from the motion trackers
        self.stream = imu.Stream(self.imu_config, self.halt_event, self.imu_data_queues)
        self.stream_thread = QThread()
        self.stream_thread.setObjectName('Stream Thread')
        self.stream.moveToThread(self.stream_thread)
        self.stream_thread.start()

    @Slot(None)
    def browse_imu_path(self):
        """
        Used to set the path of where to save the data
        """
        data_path = QFileDialog.getExistingDirectory(
            self, "Select Data Path", "", QFileDialog.Option.ShowDirsOnly
        )
        if data_path:
            self.imu_path_input.setText(data_path)
            self.imu_path = data_path

    @Slot(None)
    async def scan_for_devices(self):
        # Enable/disable buttons
        self.scan_button.setText(" Scanning...")
        self.scan_button.setEnabled(False)
        self.start_button.setEnabled(False)
        # Wait for the scan to finish, then execute the scan_done function
        self.log.info("Starting device scan")
        await self.imu_scanner.scan_for_devices()
        self.log.info("Completed device scan")
        self.scan_done()

    def scan_done(self):
        # Clear the device lists
        for checkbox in self.checkboxes:
            checkbox.deleteLater()
        for indicator in self.indicators:
            indicator.deleteLater()
        self.checkboxes = []
        self.indicators = []

        # Sort the scanned devices alphabetically by device name
        self.imu_scanner.scanned_devices = sorted(self.imu_scanner.scanned_devices, key=lambda device: device.get_id())
        
        # Create checkboxes for each device
        for device in self.imu_scanner.scanned_devices:
            # Create layout for each device
            device_layout = QHBoxLayout()

            # Create checkbox for each device
            device_name = device.get_id()
            checkbox = QCheckBox(device_name)
            checkbox.setFont(QFont("Arial", 12))
            checkbox.setChecked(True)
            device_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
            
            # Create connection status indicator for each device
            indicator = ConnectionIndicator()
            device_layout.addWidget(indicator)
            self.indicators.append(indicator)
            
            # Add the device layout to the frame
            self.device_frame_layout.addLayout(device_layout)
        
        # Reset the buttons
        self.scan_button.setText(" Device Scan")
        self.scan_button.setEnabled(True)
        if self.imu_scanner.scanned_devices:
            self.start_button.setEnabled(True)
        else:
            self.start_button.setEnabled(False)

    def recording_devices_selected(self):
        if len(self.checked_devices) > self.imu_config.max_active_connections:
            # Too many devices selected, show the message box
            QMessageBox.warning(self, "Warning",
                f"Too many devices selected for recording. \nMax connections allowed: {self.imu_config.max_active_connections}",
                QMessageBox.StandardButton.Ok)
            return False
        elif len(self.checked_devices) == 0:
            # No item selected, show the message box
            QMessageBox.warning(self, "Warning",
                "Please select devices for recording",
                QMessageBox.StandardButton.Ok)
            return False
        else:
            return True

    @Slot(None)
    async def start_recording(self):
        # Check if any recording devices are selected
        self.checked_devices = {
            checkbox.text(): (device, indicator) for device, checkbox, indicator 
            in zip(self.imu_scanner.scanned_devices, self.checkboxes, self.indicators) if checkbox.isChecked()
        }
        if not self.recording_devices_selected():
            return
        
        # Write session data to the log
        self.log.info("Starting recording")
        self.log.info(f"Saving data to {self.imu_path}")
        
        # Start the data stream
        self.stream.start(self.checked_devices, self.imu_path)
        
        # Enable/disable buttons
        self.start_button.setText(" Recording")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.scan_button.setEnabled(False)
    
    @Slot(None)
    async def stop_recording(self):
        # Set global halt event
        self.halt_event.set()

        # Stop the prediction and data stream
        await self.stream.stop()
        self.log.info("Stopped recording")
        
        # Clear halt event
        self.halt_event.clear()

        # Reset the buttons and indicators
        for indicator in self.indicators:
            indicator.reset()
        self.start_button.setText(" Start")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.scan_button.setEnabled(True)

    @Slot(QEvent)
    def closeEvent(self, event):
        '''Handle the close event (e.g., ask for confirmation, save data, etc.)'''
        # Shutdown the application
        event.setAccepted(False)
        asyncio.ensure_future(self.closeApplication(event))
        app = QApplication.instance()
        if app is not None:
            while not event.isAccepted():
                app.processEvents()
            self.log.info("Closing application")
            app.quit()
    
    @Slot(QEvent)
    async def closeApplication(self, event):
        # Set global halt event
        self.halt_event.set()
        # Stop threads and processes
        await self.stream.stop()
        self.stream_thread.quit()
        event.accept()
