"""
BBL Format Specifications and Constants
Based on Betaflight/INAV blackbox format research
"""

from enum import IntEnum
from typing import Dict, Any

# BBL File Header Constants
BBL_HEADER_SIGNATURE = b'H'
BBL_LOG_START_MARKER = b'S'
BBL_LOG_END_MARKER = b'E'

# Frame Types
class FrameType(IntEnum):
    INTRA_FRAME = ord('I')      # Full frame with all fields
    INTER_FRAME = ord('P')      # Predictive frame with deltas
    SLOW_FRAME = ord('S')       # Slow data frame
    GPS_FRAME = ord('G')        # GPS data frame
    GPS_HOME_FRAME = ord('H')   # GPS home frame
    EVENT_FRAME = ord('E')      # Event frame

# Field Types and Encodings
class FieldEncoding(IntEnum):
    SIGNED_VB = 0      # Variable-length signed integer
    UNSIGNED_VB = 1    # Variable-length unsigned integer
    NEG_14BIT = 3      # Negative 14-bit value
    TAG8_8SVB = 6      # Tag + 8-bit + signed variable byte
    TAG2_3S32 = 7      # Tag + 2-bit + 3x signed 32-bit
    TAG8_4S16 = 8      # Tag + 8-bit + 4x signed 16-bit
    NULL = 9           # Null encoding

# Common Field Names
GYRO_FIELDS = ['gyroADC[0]', 'gyroADC[1]', 'gyroADC[2]']
ACCEL_FIELDS = ['accSmooth[0]', 'accSmooth[1]', 'accSmooth[2]']
MOTOR_FIELDS = ['motor[0]', 'motor[1]', 'motor[2]', 'motor[3]']
RC_FIELDS = ['rcCommand[0]', 'rcCommand[1]', 'rcCommand[2]', 'rcCommand[3]']

# Scaling factors (typical values, may vary by firmware)
GYRO_SCALE = 1.0 / 16.4  # Convert to degrees/second
ACCEL_SCALE = 1.0 / 512.0  # Convert to G
MOTOR_SCALE = 1.0  # Motor values are typically 1000-2000

# Predictor types for delta compression
class PredictorType(IntEnum):
    ZERO = 0           # Previous value was zero
    STRAIGHT_LINE = 1  # Linear prediction
    AVERAGE_2 = 2      # Average of last 2 values
    MINTHROTTLE = 3    # Minimum throttle value
    MOTOR_0 = 4        # Based on motor[0]
    INCREMENT = 5      # Increment from previous
    HOME_COORD = 6     # GPS home coordinate
    LAST_MAIN_FRAME_TIME = 7  # Time from last main frame
    MINMOTOR = 8       # Minimum motor value
    AVERAGE_3 = 9      # Average of last 3 values

# Default field definitions for common frame types
DEFAULT_FIELD_DEFS = {
    'I': {  # Intra frame
        'loopIteration': {'encoding': FieldEncoding.UNSIGNED_VB, 'predictor': PredictorType.INCREMENT},
        'time': {'encoding': FieldEncoding.UNSIGNED_VB, 'predictor': PredictorType.STRAIGHT_LINE},
        'gyroADC[0]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'gyroADC[1]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'gyroADC[2]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'accSmooth[0]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'accSmooth[1]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'accSmooth[2]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
    },
    'P': {  # Inter frame (same as intra but with predictive encoding)
        'loopIteration': {'encoding': FieldEncoding.UNSIGNED_VB, 'predictor': PredictorType.INCREMENT},
        'time': {'encoding': FieldEncoding.UNSIGNED_VB, 'predictor': PredictorType.STRAIGHT_LINE},
        'gyroADC[0]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'gyroADC[1]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'gyroADC[2]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'accSmooth[0]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'accSmooth[1]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
        'accSmooth[2]': {'encoding': FieldEncoding.SIGNED_VB, 'predictor': PredictorType.ZERO},
    }
}