import numpy as np
from vqf import VQF
import math


class Quaternion:
    @staticmethod
    def quat_multiply(q, r):
        """
        Perform quaternion multiplication.

        Multiply two quaternions 'q' and 'r' element-wise.
        The output represents the rotation of 'r' in the frame of 'q'.

        Parameters:
        - q: First quaternion as an array with shape (4,) or (N, 4)
        - r: Second quaternion as an array with shape (4,) or (N, 4)

        Returns:
        - An array containing the resulting quaternion(s).
          - If both 'q' and 'r' are 1D arrays (shape: (4,)), returns a single quaternion as a 1D array (shape: (4,))
          - If either 'q' or 'r' is a 2D array and the other is a 1D array,
            returns an array of resulting quaternions as a 2D array (shape: (N, 4))
          - If both 'q' and 'r' are 2D arrays (shape: (N, 4)),
            returns an array of resulting quaternions as a 2D array (shape: (N, 4))
        """
        q = np.array(q)
        r = np.array(r)

        if q.ndim == 2 and r.ndim == 2 and q.shape[1] == 4 and r.shape[1] == 4:
            return Quaternion.quat_product(q, r)
        elif q.ndim == 1 and r.ndim == 2 and q.shape[0] == 4 and r.shape[1] == 4:
            q_extended = np.tile(q, (len(r), 1))
            return Quaternion.quat_product(q_extended, r)
        elif q.ndim == 2 and r.ndim == 1 and q.shape[1] == 4 and r.shape[0] == 4:
            r_extended = np.tile(r, (len(q), 1))
            return Quaternion.quat_product(q, r_extended)
        elif q.ndim == 1 and r.ndim == 1 and q.shape[0] == 4 and r.shape[0] == 4:
            q_extended = np.reshape(q, (1, 4))
            r_extended = np.reshape(r, (1, 4))
            return Quaternion.quat_product(q_extended, r_extended)[0]
        else:
            raise ValueError("Quaternion must either have the shape (4,) or (N, 4)")

    @staticmethod
    def quat_product(q, r):
        """
        Multiply two sets of quaternions element-wise.

        Parameters:
        - q: Array containing the first set of quaternions of shape (N,4)
        - r: Array containing the second set of quaternions of shape (N,4)

        Returns:
        - An array containing the resulting quaternions of shape (N,4)
        """
        q0 = q[:, 0] * r[:, 0] - q[:, 1] * r[:, 1] - q[:, 2] * r[:, 2] - q[:, 3] * r[:, 3]
        q1 = q[:, 1] * r[:, 0] + q[:, 0] * r[:, 1] - q[:, 3] * r[:, 2] + q[:, 2] * r[:, 3]
        q2 = q[:, 2] * r[:, 0] + q[:, 3] * r[:, 1] + q[:, 0] * r[:, 2] - q[:, 1] * r[:, 3]
        q3 = q[:, 3] * r[:, 0] - q[:, 2] * r[:, 1] + q[:, 1] * r[:, 2] + q[:, 0] * r[:, 3]

        return np.column_stack((q0, q1, q2, q3))

    @staticmethod
    def quat_conjugate(q):
        """
        Calculate the conjugate of a quaternion.

        Parameters:
        - q: A list or array containing the four elements of the quaternion or a quaternion time series

        Returns:
        - An array containing the four elements of the resulting quaternion or a conjugated time series
        """
        return q * np.array([1, -1, -1, -1])

    @staticmethod
    def rotate_coordinate_frame(target_initial_quat, quats):
        """
        Rotate array of quaternions into new coordinate frame such that the initial quaternion of the rotated array
        matches the target quaternion.

        Parameters:
        target_initial_quat: target for initial quaternion of rotated array
        quats: array of quaternions

        Returns:
        rotated_quats: rotated array of quaternions
        """
        rotation = Quaternion.quat_multiply(target_initial_quat, Quaternion.quat_conjugate(quats[0, :]))
        return Quaternion.rotate_quaternions(rotation, quats)

    @staticmethod
    def rotate_quaternions(rotation, quats):
        """
        Rotate array of quaternions around given rotation quaternion.
        """
        return Quaternion.quat_multiply(rotation, quats)

    @staticmethod
    def rotate_vector_by_quat(vector, q):
        """
        Rotate a 3D vector or a batch of 3D vectors using a quaternion or batch of quaternions.

        Parameters:
        - vector: 3D vector or an array of 3D vectors to be rotated
        - q: Quaternion or an array of quaternions to rotate by

        Returns:
          - If both 'vector' and 'q' are arrays with shape (N,3) and (N,4) respectively, returns an array
            containing the rotated vectors with shape (N,3)
          - If 'vector' is a single vector (shape: (3,)) and 'q' is a single quaternion (shape: (4,)),
            returns a single rotated vector as a list (shape: (3,))
          - If either 'vector' or 'q' is an array and the other is a single vector/quaternion, it extends the
            single vector/quaternion to match the shape of the array and performs batch rotation
        """
        vector = np.array(vector)
        q = np.array(q)
        if vector.ndim == 2 and q.ndim == 2 and vector.shape[1] == 3 and q.shape[1] == 4:
            return Quaternion.rotate_vectors(vector, q)
        elif vector.ndim == 2 and q.ndim == 1 and vector.shape[1] == 3 and q.shape[0] == 4:
            q_extended = np.tile(q, (len(vector), 1))
            return Quaternion.rotate_vectors(vector, q_extended)
        elif vector.ndim == 1 and q.ndim == 2 and vector.shape[0] == 3 and q.shape[1] == 4:
            vector_extended = np.tile(vector, (len(q), 1))
            return Quaternion.rotate_vectors(vector_extended, q)
        elif vector.ndim == 1 and q.ndim == 1 and vector.shape[0] == 3 and q.shape[0] == 4:
            q_extended = np.reshape(q, (1, 4))
            vector_extended = np.reshape(vector, (1, 3))
            return Quaternion.rotate_vectors(vector_extended, q_extended)[0]
        else:
            raise ValueError("Quaternion must either have the shape (4,) or (N, 4) and vector must have the shape "
                             "(3,) or (N, 3)")

    @staticmethod
    def rotate_vectors(vectors, quats):
        """
        Rotate a batch of 3D vectors using a batch of quaternions.

        Parameters:
        - vectors: Array of shape (N,3) containing 3D vectors to be rotated
        - quats: Array of shape (N,4) containing quaternions to rotate the vectors by

        Returns:
        - Array of shape (N,3) containing the rotated 3D vectors after applying quaternion rotation

        The function performs batch quaternion rotation on a batch of 3D vectors using corresponding quaternions.
        It first calculates the conjugate of the input quaternions, then represents the input vectors as quaternions
        with zero scalar parts. After performing quaternion multiplication, it extracts and returns the vector parts
        of the resulting rotated quaternions.
        """
        quats_conj = Quaternion.quat_conjugate(quats)

        # Represent vectors as quaternions with zero scalar parts
        vectors_extended = np.hstack((np.zeros((len(quats), 1)), vectors))

        temp = Quaternion.quat_multiply(quats, vectors_extended)
        rotated_vectors = Quaternion.quat_multiply(temp, quats_conj)

        # Extract and return the vector parts of the rotated quaternions
        rotated_vectors = rotated_vectors[:, 1:]

        return rotated_vectors
    
    @staticmethod
    def offline_vqf(dt, acc, gyr, mag=None):
        '''
        Perform one-off VQF estimation using accelerometer, 
        gyroscope and (optional) magnetometer data
        
        Parameters:
        - dt      Sampling rate of the period               [s]
        - acc     (N,3) array of accelerometer measurements [m/s^2]
        - gyr     (N,3) array of gyroscope measurements     [rad/s]
        - (mag)   (N,3) array of magnetometer measurements  [arb. units]
        Returns:
        - quat    (N,4) array of updated quaternions (scalar-first)
        - rest    (N,) array of rest detection state
        - (dist)  (N,) array of magnetic disturbance state
        '''
        return Quaternion.update_vqf(VQF(dt), acc, gyr, mag)
    
    @staticmethod
    def update_vqf(vqf, acc, gyr, mag=None):
        '''
        Perform live VQF estimation using accelerometer, 
        gyroscope and (optional) magnetometer data
        
        Parameters:
        - vqf     VQF class object
        - acc     (N,3) array of accelerometer measurements [m/s^2]
        - gyr     (N,3) array of gyroscope measurements     [rad/s]
        - (mag)   (N,3) array of magnetometer measurements  [arb. units]
        Returns:
        - quat    (N,4) array of updated quaternions (scalar-first)
        - rest    (N,) array of rest detection state
        - (dist)  (N,) array of magnetic disturbance state
        '''
        # Copy data to NumPy array and update VQF estimation
        acc = np.ascontiguousarray(acc)
        gyr = np.ascontiguousarray(gyr)
        
        # Return updated quaternion, rest detection and magnetic disturbance detection data
        if mag is not None and len(mag)>0:
            mag = np.ascontiguousarray(mag)
            out = vqf.updateBatch(gyr, acc, mag)
            return out["quat9D"], out["restDetected"], out["magDistDetected"]
        else:
            out = vqf.updateBatch(gyr, acc)
            return out["quat6D"], out["restDetected"]
    
    @staticmethod
    def quat_to_rot_matrix(q):
        """Convert a quaternion into a rotation matrix."""
        w, x, y, z = q
        return np.array(
            [
                [
                    1 - 2 * y * y - 2 * z * z,
                    2 * x * y - 2 * z * w,
                    2 * x * z + 2 * y * w,
                ],
                [
                    2 * x * y + 2 * z * w,
                    1 - 2 * x * x - 2 * z * z,
                    2 * y * z - 2 * x * w,
                ],
                [
                    2 * x * z - 2 * y * w,
                    2 * y * z + 2 * x * w,
                    1 - 2 * x * x - 2 * y * y,
                ],
            ]
        )

    @staticmethod
    def quat_to_euler(quat):
        """
        Convert the quaternion or list of quaternions to euler
        angles (roll, pitch, yaw). the output will be in radians!
        
        - roll is rotation around x in radians (counterclockwise)
        - pitch is rotation around y in radians (counterclockwise)
        - yaw is rotation around z in radians (counterclockwise)
        """
        def quaternion_to_euler(q):
            w, x, y, z = q
            t0 = +2.0 * (w * x + y * z)
            t1 = +1.0 - 2.0 * (x * x + y * y)
            roll_x = math.atan2(t0, t1)

            t2 = +2.0 * (w * y - z * x)
            t2 = min(t2, 1.0)
            t2 = max(t2, -1.0)
            pitch_y = math.asin(t2)

            # t5 = math.sqrt(1 + 2 * (w * y - x * z))
            # t6 = math.sqrt(1 - 2 * (w * y - x * z))
            # pitch_y = -math.pi/2 + 2 * math.atan2(t5, t6)

            t3 = +2.0 * (w * z + x * y)
            t4 = +1.0 - 2.0 * (y * y + z * z)
            yaw_z = math.atan2(t3, t4)

            return roll_x, pitch_y, yaw_z  # in radians
        
        if np.ndim(quat) > 1:
            result = np.zeros((np.size(quat, 0), 3))
            for i in range(np.size(quat, 0)):
                result[i, :] = quaternion_to_euler(quat[i, :])
        else:
            result = quaternion_to_euler(quat)
        return result

    @staticmethod
    def euler_to_quat(euler):
        (roll, pitch, yaw) = (euler[0], euler[1], euler[2])
        qw = (np.cos(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) +
              np.sin(roll / 2) * np.sin(pitch / 2) * np.sin(yaw / 2))
        qx = (np.sin(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) -
              np.cos(roll / 2) * np.sin(pitch / 2) * np.sin(yaw / 2))
        qy = (np.cos(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2) +
              np.sin(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2))
        qz = (np.cos(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2) -
              np.sin(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2))
        return [qw, qx, qy, qz]
