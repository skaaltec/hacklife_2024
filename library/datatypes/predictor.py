import numpy as np
from typing import Tuple
from abc import ABC, abstractmethod

class Predictor(ABC):
    """
    Abstract base class for a Predictor.

    This class defines the interface for a predictor that classifies time-series data 
    from accelerometers, gyroscopes, and/or quaternion data. Subclasses must implement 
    the `classify` method to provide specific classification logic.
    
    Methods
    -------
    classify(ts: np.ndarray, acc: np.ndarray, gyro: np.ndarray, quat: np.ndarray) -> Tuple[bool, float]
        Abstract method to classify the given sensor data.
        Args:
            ts:                 Input timestamp data (system_time, device_time)
            acc:                Input acceleration data (acc_x, acc_y, acc_z)
            gyro:               Input gyroscope data (gyro_x, gyro_y, gyro_z)
            quat:               Input quaternions in scalar-first format (q_w, q_x, q_y, q_z)
        Returns:
            prediction:         Boolean value if prediction confidence exceeds threshold (bool)
            confidence:         Normalized prediction confidence level in the range [0–1] (float)
    """
    @abstractmethod
    def classify(
        self, 
        ts: np.ndarray, 
        acc: np.ndarray, 
        gyro: np.ndarray, 
        quat: np.ndarray
    ) -> Tuple[bool, float]: ... # prediction, confidence