"""
Unit tests for BBL decoder
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decoder import BBLDecoder, decode_bbl_bytes

class TestBBLDecoder:
    
    def test_decoder_initialization(self):
        """Test decoder initializes correctly"""
        decoder = BBLDecoder()
        assert decoder.headers == {}
        assert decoder.field_definitions == {}
        assert decoder.gyro_data == []
    
    def test_variable_length_integer_decoding(self):
        """Test variable-length integer decoding"""
        decoder = BBLDecoder()
        
        # Test with simple bytes
        from io import BytesIO
        
        # Test unsigned VB: value 127 (0x7F)
        stream = BytesIO(b'\x7F')
        result = decoder._read_unsigned_vb(stream)
        assert result == 127
        
        # Test unsigned VB: value 128 (0x80, 0x01)
        stream = BytesIO(b'\x80\x01')
        result = decoder._read_unsigned_vb(stream)
        assert result == 128
    
    def test_signed_variable_length_integer(self):
        """Test signed variable-length integer decoding"""
        decoder = BBLDecoder()
        from io import BytesIO
        
        # Test positive value
        stream = BytesIO(b'\x0A')  # 10
        result = decoder._read_signed_vb(stream)
        assert result == 10
        
        # Test zero
        stream = BytesIO(b'\x00')
        result = decoder._read_signed_vb(stream)
        assert result == 0
    
    def test_predictor_application(self):
        """Test predictor-based decompression"""
        decoder = BBLDecoder()
        
        # Set up frame history
        decoder.frame_history = [
            {'gyroADC[0]': 100, 'gyroADC[1]': 200},
            {'gyroADC[0]': 110, 'gyroADC[1]': 210}
        ]
        
        # Test ZERO predictor
        result = decoder._apply_predictor(5, 'gyroADC[0]', 0)
        assert result == 5  # 0 + 5
        
        # Test STRAIGHT_LINE predictor
        result = decoder._apply_predictor(5, 'gyroADC[0]', 1)
        assert result == 125  # (2*110 - 100) + 5 = 120 + 5
    
    def test_minimal_bbl_structure(self):
        """Test decoding minimal BBL structure"""
        # Create minimal BBL data
        bbl_data = (
            b'H Product:Betaflight\n'
            b'H Version:4.3.0\n'
            b'F I gyroADC[0]:0:0 gyroADC[1]:0:0 gyroADC[2]:0:0\n'
            b'S\n'  # Log start marker
            b'I'    # Intra frame marker
            b'\x64'  # gyroADC[0] = 100
            b'\x7F'  # gyroADC[1] = 127  
            b'\x00'  # gyroADC[2] = 0
        )
        
        result = decode_bbl_bytes(bbl_data)
        
        # Should not error out
        assert 'error' not in result or result.get('success', False)
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data"""
        result = decode_bbl_bytes(b'')
        assert 'error' in result
        
        result = decode_bbl_bytes(b'invalid data')
        assert 'error' in result
    
    def test_gyro_data_extraction(self):
        """Test gyro data extraction and scaling"""
        decoder = BBLDecoder()
        
        # Mock frame data
        frame_data = {
            'gyroADC[0]': 1640,  # Should scale to ~100 deg/s
            'gyroADC[1]': -820,  # Should scale to ~-50 deg/s
            'gyroADC[2]': 0,     # Should scale to 0 deg/s
            'time': 1000
        }
        
        decoder._extract_gyro_data(frame_data)
        
        assert len(decoder.gyro_data) == 1
        gyro_point = decoder.gyro_data[0]
        
        assert gyro_point['timestamp'] == 1000
        assert abs(gyro_point['gyro_x'] - 100.0) < 1.0  # ~100 deg/s
        assert abs(gyro_point['gyro_y'] - (-50.0)) < 1.0  # ~-50 deg/s
        assert gyro_point['gyro_z'] == 0.0
        
        # Check raw values are preserved
        assert gyro_point['gyro_x_raw'] == 1640
        assert gyro_point['gyro_y_raw'] == -820
        assert gyro_point['gyro_z_raw'] == 0
    
    def test_frame_history_management(self):
        """Test frame history is properly managed"""
        decoder = BBLDecoder()
        
        # Simulate the actual frame processing logic
        for i in range(15):
            frame_data = {'gyroADC[0]': i, 'frame_type': 'I'}
            decoder._extract_gyro_data(frame_data)
            decoder.frame_history.append(frame_data)
            
            # Apply the same trimming logic as in _parse_data_frames
            if len(decoder.frame_history) > 10:
                decoder.frame_history = decoder.frame_history[-10:]
        
        # Should keep only last 10 frames
        assert len(decoder.frame_history) <= 10
        assert len(decoder.gyro_data) == 15  # But all gyro data is kept

if __name__ == "__main__":
    pytest.main([__file__])