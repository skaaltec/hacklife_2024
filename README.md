# SmartVNS Hacklife<3 2024 Challenge
---
# Installation:

The application works under MacOS, Linux and Windows.

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

To run, execute `main.py` within your virtual environment:
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

To run, execute `main.py` within your virtual environment:
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
2. Connect to an IMU and analyze the output .csv files in the output folder. Compare to the cleaned file samples found here [[1](#links)], note that the data is aligned in time and converted to SI units.
3. Use the `scaling_factors` found in `stream.py` to write a script that reads the raw output data from the streaming application, converts it to SI units and aligns the timestamps between devices, e.g. through cross-correlation of a specific calibration movement at the start of the recording. **Bonus:** Implement a TCP/UDP data streaming interface in the GUI to live stream the data to your script instead.
4. Read up on different representations of spatial rotations, particularly quaternions [[2](#links)]. Implement an efficient quaternion estimation. You can use the helper methods found in `./library/quaternions.py`, or alternatively use the available quaternion estimation implementation based on VQF [[3](#links)]. **Bonus:** Implement quaternion estimation using an Extended Kalman Filter [[4](#links)], with a particular focus on computing efficiency.
5. The simplest movement compensation method is a reference frame transformation of the wrist IMU in the body frame given by the trunk IMU. Write a method to perform a transformation of IMU data from the global frame into the body frame. **Bonus:** Read into position & orientation estimation from IMU data [[5](#links)]
6. Explore the provided dataset of healthy users performing different upper-limb tasks without restriction (**natural**), with restricted elbow motion (fixed 80° flexion = **comp**), and finally restricted elobw and wrist (**comp_WE**). Dataset is available in file samples `Course data.zip` [[1](#links)] and slideshow is giving more details about the dataset. Restricted motion may not exactly correspond to compensation label but should induce more compensation strategy in comparison to natural movement. You can use joint angles from mocap to label simple compensation movement, or use clustering techniques **Bonus:** Propose an automatic labeling strategy for compensation based on your exploration.
7. Implement a compensation motion detection algorithm that generates Boolean labels from motion tracker data of the trunk IMU. **Bonus:** Clean and summarize your algorithm as a class implementation of the Predictor abstract base class (`./library/datatypes/predictor.py`) for use in a real-time application. **Bonus (2):** Assess the performance of your detection based on the task 6. 
8. Implement a motion detection algorithm that generates Boolean labels from motion tracker data of the wrist IMU. Reframe the data to the body frame in order to account for unwanted compensation movements. **Bonus:** Clean and summarize your algorithm as a class implementation of the Predictor abstract base class (`./library/datatypes/predictor.py`) for use in a real-time application.
9. Implement a unified motion detection algorithm that generates Boolean labels from motion tracker data of both the wrist and trunk IMUs. The algorithm should return a `True` label only if the movement was performed with little or no compensatory movements from the trunk.
10. Submit all code either as a fork of this repo, or uploaded here [[1](#links)]

## Links
[1] Sample datasets and code submissions (password: `hacklife<3`): https://polybox.ethz.ch/index.php/s/OMkVh5Mhgq00tYG

[2] Spatial representation and quaternions: https://eater.net/quaternions / 

[3] Versatile Quaternion Filter: https://github.com/dlaidig/vqf

[4] Extended Kalman Filter: https://www.kaggle.com/code/hrshtt/kalman-filters-and-imus-starter / https://ahrs.readthedocs.io/en/latest/filters/ekf.html

[5] Overview IMU position & orientation estimation: https://arxiv.org/pdf/1704.06053


---
Based on `BLELog` by Philipp Schilk, 2022 (PBL, ETH Zuerich) and the [bleak](https://github.com/hbldh/bleak) cross-platform Bluetooth backend.
