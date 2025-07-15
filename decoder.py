"""
BBL (Betaflight Blackbox Log) Decoder
Implements proper BBL format parsing based on technical specifications
"""

import struct
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
from bitstring import BitStream
from specs import *

class BBLDecoder:
    def __init__(self):
        self.headers = {}
        self.field_definitions = {}
        self.frame_history = []
        self.current_frame_data = {}
        self.gyro_data = []
        
    def decode_file(self, file_path: str) -> Dict[str, Any]:
        """Decode a BBL file and extract gyro data"""
        try:
            with open(file_path, 'rb') as f:
                return self._decode_stream(f)
        except Exception as e:
            return {'error': f'Failed to decode file: {str(e)}', 'gyro_data': []}
    
    def decode_bytes(self, data: bytes) -> Dict[str, Any]:
        """Decode BBL data from bytes"""
        try:
            from io import BytesIO
            stream = BytesIO(data)
            return self._decode_stream(stream)
        except Exception as e:
            return {'error': f'Failed to decode bytes: {str(e)}', 'gyro_data': []}
    
    def _decode_stream(self, stream: BinaryIO) -> Dict[str, Any]:
        """Main decoding logic for BBL stream"""
        self.headers = {}
        self.field_definitions = {}
        self.frame_history = []
        self.current_frame_data = {}
        self.gyro_data = []
        
        # Parse headers first
        if not self._parse_headers(stream):
            return {'error': 'Failed to parse headers', 'gyro_data': []}
        
        # Parse field definitions
        if not self._parse_field_definitions(stream):
            return {'error': 'Failed to parse field definitions', 'gyro_data': []}
        
        # Parse data frames
        frame_count = self._parse_data_frames(stream)
        
        return {
            'success': True,
            'headers': self.headers,
            'field_definitions': self.field_definitions,
            'frame_count': frame_count,
            'gyro_data': self.gyro_data
        }
    
    def _parse_headers(self, stream: BinaryIO) -> bool:
        """Parse BBL file headers"""
        try:
            while True:
                line = self._read_line(stream)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Check for header marker
                if line.startswith(b'H '):
                    header_data = line[2:].decode('utf-8', errors='ignore')
                    if ':' in header_data:
                        key, value = header_data.split(':', 1)
                        self.headers[key.strip()] = value.strip()
                
                # Check for log start marker
                elif line == BBL_LOG_START_MARKER:
                    # Found start marker, stream is now positioned for frame data
                    return True
                
                # Check for field definition
                elif line.startswith(b'F '):
                    # Field definitions come after headers, go back and let field parser handle
                    stream.seek(stream.tell() - len(line) - 1)  # Go back
                    return True
            
            return len(self.headers) > 0
        except Exception as e:
            print(f"Header parsing error: {e}")
            return False
    
    def _parse_field_definitions(self, stream: BinaryIO) -> bool:
        """Parse field definitions from headers"""
        try:
            # Parse field definitions from headers
            field_names = {}
            field_encodings = {}
            field_predictors = {}
            field_signed = {}
            
            # Extract field information from headers
            for key, value in self.headers.items():
                if key.startswith('Field ') and key.endswith(' name'):
                    frame_type = key.split()[1]
                    field_names[frame_type] = value.split(',')
                elif key.startswith('Field ') and key.endswith(' encoding'):
                    frame_type = key.split()[1]
                    field_encodings[frame_type] = [int(x) for x in value.split(',')]
                elif key.startswith('Field ') and key.endswith(' predictor'):
                    frame_type = key.split()[1]
                    field_predictors[frame_type] = [int(x) for x in value.split(',')]
                elif key.startswith('Field ') and key.endswith(' signed'):
                    frame_type = key.split()[1]
                    field_signed[frame_type] = [int(x) for x in value.split(',')]
            
            # Build field definitions
            for frame_type in field_names:
                if frame_type not in self.field_definitions:
                    self.field_definitions[frame_type] = {}
                
                names = field_names[frame_type]
                encodings = field_encodings.get(frame_type, [0] * len(names))
                predictors = field_predictors.get(frame_type, [0] * len(names))
                
                for i, name in enumerate(names):
                    encoding = encodings[i] if i < len(encodings) else 0
                    predictor = predictors[i] if i < len(predictors) else 0
                    
                    self.field_definitions[frame_type][name] = {
                        'encoding': encoding,
                        'predictor': predictor
                    }
            
            # The field definitions are already parsed from headers
            # No need to read more from stream since we have all we need
            
            # Use default field definitions if none found
            if not self.field_definitions:
                self.field_definitions = DEFAULT_FIELD_DEFS.copy()
            
            return True
        except Exception as e:
            print(f"Field definition parsing error: {e}")
            return False
    
    def _parse_data_frames(self, stream: BinaryIO) -> int:
        """Parse data frames and extract gyro data"""
        frame_count = 0
        
        try:
            while True:
                # Read frame marker
                marker = stream.read(1)
                if not marker:
                    break
                
                frame_type = marker.decode('ascii', errors='ignore')
                
                if frame_type in ['I', 'P']:  # Main frames with gyro data
                    frame_data = self._parse_main_frame(stream, frame_type)
                    if frame_data:
                        self._extract_gyro_data(frame_data)
                        self.frame_history.append(frame_data)
                        frame_count += 1
                        
                        # Keep only recent history for prediction
                        if len(self.frame_history) > 10:
                            self.frame_history = self.frame_history[-10:]
                
                elif frame_type == 'S':  # Slow frame
                    self._skip_slow_frame(stream)
                
                elif frame_type in ['G', 'H']:  # GPS frames
                    self._skip_gps_frame(stream)
                
                elif frame_type == 'E':  # Event frame
                    self._skip_event_frame(stream)
                
                else:
                    # Unknown frame type, stop parsing
                    break
        
        except Exception as e:
            print(f"Frame parsing error: {e}")
        
        return frame_count
    
    def _parse_main_frame(self, stream: BinaryIO, frame_type: str) -> Optional[Dict[str, Any]]:
        """Parse main frame (I or P type) containing gyro data"""
        try:
            frame_data = {'frame_type': frame_type}
            field_defs = self.field_definitions.get(frame_type, {})
            
            # Read frame data based on field definitions
            for field_name, field_def in field_defs.items():
                try:
                    value = self._read_field_value(stream, field_def['encoding'])
                    
                    # Apply predictor if this is a P frame
                    if frame_type == 'P' and self.frame_history:
                        value = self._apply_predictor(value, field_name, field_def['predictor'])
                    
                    frame_data[field_name] = value
                    
                except Exception as e:
                    # If we can't read a field, try to continue
                    print(f"Error reading field {field_name}: {e}")
                    break
            
            return frame_data if len(frame_data) > 1 else None
            
        except Exception as e:
            print(f"Main frame parsing error: {e}")
            return None
    
    def _read_field_value(self, stream: BinaryIO, encoding: int) -> int:
        """Read a field value based on its encoding"""
        if encoding == FieldEncoding.SIGNED_VB:
            return self._read_signed_vb(stream)
        elif encoding == FieldEncoding.UNSIGNED_VB:
            return self._read_unsigned_vb(stream)
        elif encoding == FieldEncoding.NEG_14BIT:
            return self._read_neg_14bit(stream)
        else:
            # Default to signed variable byte
            return self._read_signed_vb(stream)
    
    def _read_signed_vb(self, stream: BinaryIO) -> int:
        """Read signed variable-length integer"""
        try:
            result = 0
            shift = 0
            
            while True:
                byte_data = stream.read(1)
                if not byte_data:
                    return 0
                
                byte_val = byte_data[0]
                result |= (byte_val & 0x7F) << shift
                
                if (byte_val & 0x80) == 0:
                    break
                
                shift += 7
                if shift > 28:  # Prevent infinite loop
                    break
            
            # Convert to signed
            if result & (1 << (shift + 6)):
                result -= (1 << (shift + 7))
            
            return result
        except:
            return 0
    
    def _read_unsigned_vb(self, stream: BinaryIO) -> int:
        """Read unsigned variable-length integer"""
        try:
            result = 0
            shift = 0
            
            while True:
                byte_data = stream.read(1)
                if not byte_data:
                    return 0
                
                byte_val = byte_data[0]
                result |= (byte_val & 0x7F) << shift
                
                if (byte_val & 0x80) == 0:
                    break
                
                shift += 7
                if shift > 28:  # Prevent infinite loop
                    break
            
            return result
        except:
            return 0
    
    def _read_neg_14bit(self, stream: BinaryIO) -> int:
        """Read negative 14-bit value"""
        try:
            data = stream.read(2)
            if len(data) < 2:
                return 0
            
            value = struct.unpack('<H', data)[0]
            return -(value & 0x3FFF)
        except:
            return 0
    
    def _apply_predictor(self, delta: int, field_name: str, predictor_type: int) -> int:
        """Apply predictor to delta value for P frames"""
        if not self.frame_history:
            return delta
        
        last_frame = self.frame_history[-1]
        
        if predictor_type == PredictorType.ZERO:
            predicted = 0
        elif predictor_type == PredictorType.STRAIGHT_LINE:
            if len(self.frame_history) >= 2:
                predicted = 2 * last_frame.get(field_name, 0) - self.frame_history[-2].get(field_name, 0)
            else:
                predicted = last_frame.get(field_name, 0)
        elif predictor_type == PredictorType.AVERAGE_2:
            if len(self.frame_history) >= 2:
                predicted = (last_frame.get(field_name, 0) + self.frame_history[-2].get(field_name, 0)) // 2
            else:
                predicted = last_frame.get(field_name, 0)
        elif predictor_type == PredictorType.INCREMENT:
            predicted = last_frame.get(field_name, 0) + 1
        else:
            predicted = last_frame.get(field_name, 0)
        
        return predicted + delta
    
    def _extract_gyro_data(self, frame_data: Dict[str, Any]):
        """Extract and scale gyro data from frame"""
        gyro_x = frame_data.get('gyroADC[0]', 0)
        gyro_y = frame_data.get('gyroADC[1]', 0)
        gyro_z = frame_data.get('gyroADC[2]', 0)
        
        # Scale gyro values to degrees/second
        gyro_x_scaled = gyro_x * GYRO_SCALE
        gyro_y_scaled = gyro_y * GYRO_SCALE
        gyro_z_scaled = gyro_z * GYRO_SCALE
        
        timestamp = frame_data.get('time', len(self.gyro_data))
        
        self.gyro_data.append({
            'timestamp': timestamp,
            'gyro_x': gyro_x_scaled,
            'gyro_y': gyro_y_scaled,
            'gyro_z': gyro_z_scaled,
            'gyro_x_raw': gyro_x,
            'gyro_y_raw': gyro_y,
            'gyro_z_raw': gyro_z
        })
    
    def _skip_slow_frame(self, stream: BinaryIO):
        """Skip slow frame data"""
        # Slow frames typically have fewer fields, try to read a reasonable amount
        try:
            for _ in range(5):  # Assume max 5 fields
                self._read_signed_vb(stream)
        except:
            pass
    
    def _skip_gps_frame(self, stream: BinaryIO):
        """Skip GPS frame data"""
        try:
            for _ in range(10):  # GPS frames can have many fields
                self._read_signed_vb(stream)
        except:
            pass
    
    def _skip_event_frame(self, stream: BinaryIO):
        """Skip event frame data"""
        try:
            # Event frames are usually small
            self._read_unsigned_vb(stream)  # Event type
            self._read_unsigned_vb(stream)  # Event data
        except:
            pass
    
    def _read_line(self, stream: BinaryIO) -> bytes:
        """Read a line from the stream"""
        line = b''
        while True:
            char = stream.read(1)
            if not char or char == b'\n':
                break
            if char != b'\r':
                line += char
        return line

def decode_bbl_file(file_path: str) -> Dict[str, Any]:
    """Convenience function to decode a BBL file"""
    decoder = BBLDecoder()
    return decoder.decode_file(file_path)

def decode_bbl_bytes(data: bytes) -> Dict[str, Any]:
    """Convenience function to decode BBL data from bytes"""
    decoder = BBLDecoder()
    return decoder.decode_bytes(data)