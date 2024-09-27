# StreamLog

Based on `BLELog` by Philipp Schilk, 2022 (PBL, ETH Zuerich) and the [bleak](https://github.com/hbldh/bleak) 
cross-platform Bluetooth backend.

---

An application for streaming data from the  SmartVNS Motion Trackers over BLE.


# Installation:

StreamLog works under MacOS, Linux and Windows.

__WSL will not work due to limited HW access.__

Tested under Python 3.12.4

## Linux / MacOS:

First, clone the repository.

All dependencies can be installed via `pip` and are listed in `requirements.txt`.

It is advisable to set up a virtual environment to run this script. 

To do so, run:
```bash
# Create a new venv:
python -m venv .venv

# Activate it:
source .venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

You can always deactivate and activate this venv as follows:
```bash
# Deactivate the currently active venv:
deactivate

# Activate the venv:
source .venv/bin/activate
```

The git submodules need to be initialized and updated before running:
```bash
git submodule init

git submodule update
```

To run `StreamLog`, execute `main.py` with your venv active:
```bash
python main.py
```

## Windows:

First, clone the repository.

All dependencies can be installed via `pip` and are listed in `requirements.txt`.

It is advisable to set up a virtual environment to run this script. 

To do so, run:
```powershell
# Create a new venv:
python -m venv .venv

# Activate it:
.venv\Scripts\Activate.ps1

# Install dependencies:
pip install -r requirements.txt
```

You can always deactivate and activate this venv as follows:
```powershell
# Deactivate the currently active venv:
deactivate

# Activate the venv:
.venv\Scripts\activate
```

The git submodules need to be initialized and updated before running:
```powershell
git submodule init

git submodule update
```

To run `StreamLog`, execute `main.py` with your virtual environment active:
```powershell
python main.py
```

# Configuration:

You can adjust some basic settings to your application by modify the following file:
__./library/config.py__

It contains all connection parameters, including:

    - Device addresses and aliases
    - BLE Characteristic information
    - Connection parameters

Read the included comments for more details.

# Tasks

To get started on the algorithm implementation, you can follow the tasks below:

1. Set up your environment and familiarize yourself with the streaming application.
2. Connect to an IMU and analyze the output .csv files in the output folder. Compare to the cleaned file samples in ./sample_data, note that the data is aligned in time and converted to SI units.
3. Use the `scaling_factors` found in `stream.py` to write a script that reads the raw output data from the streaming application, converts it to SI units and aligns the timestamps between devices, e.g. through cross-correlation of a specific calibration movement at the start of the recording. **Bonus**: Implement a TCP/UDP data streaming interface in the GUI to live stream the data to your script instead.
4. Read up on different representations of spatial rotations, particularly quaternions [1]. Implement an efficient quaternion estimation. You can use the helper methods found in `./library/quaternions.py`, or alternatively use the available quaternion estimation implementation based on VQF [2]. **Bonus**: Implement quaternion estimation using an Extended Kalman Filter [3], with a particular focus on computing efficiency.
5. The simplest movement compensation method is a reference frame transformation of the wrist IMU in the body frame given by the trunk IMU. Write a method to perform a transformation of IMU data from the global frame into the body frame.
6. Implement a compensation motion detection algorithm that generates Boolean labels from motion tracker data of the trunk IMU. **Bonus** Clean and summarize your algorithm as a class implementation of the Predictor abstract base class (`./library/datatypes/predictor.py`) for use in a real-time application.
7. Implement a motion detection algorithm that generates Boolean labels from motion tracker data of the wrist IMU. Reframe the data to the body frame in order to account for unwanted compensation movements. **Bonus** Clean and summarize your algorithm as a class implementation of the Predictor abstract base class (`./library/datatypes/predictor.py`) for use in a real-time application.
8. Implement a unified motion detection algorithm that generates Boolean labels from motion tracker data of both the wrist and trunk IMUs. The algorithm should return a `True` label only if the movement was performed with little or no compensatory movements from the trunk. 
