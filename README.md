# BBL Decoder

A proper implementation of a Betaflight Blackbox Log (BBL) decoder based on technical specifications.

## Features

- **Proper BBL format parsing** with header and field definition support
- **Variable-length integer decoding** for compressed data
- **Predictor-based decompression** for delta values in P frames
- **Field definition parsing** from headers
- **Multiple frame type support** (Intra, Inter, Slow, GPS, Event)
- **Gyro data extraction** with proper scaling to degrees/second
- **Supabase Edge Function** deployment ready

## Installation

```bash
cd bbl_decoder
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install bitstring pytest supabase
```

## Usage

### Command Line

```bash
python cli.py sample_file.bbl
```

### Python API

```python
from decoder import decode_bbl_file, decode_bbl_bytes

# Decode from file
result = decode_bbl_file('flight_log.bbl')

# Decode from bytes
with open('flight_log.bbl', 'rb') as f:
    data = f.read()
result = decode_bbl_bytes(data)

# Access gyro data
if result['success']:
    for gyro_point in result['gyro_data']:
        print(f"Gyro X: {gyro_point['gyro_x']:.2f}°/s")
        print(f"Gyro Y: {gyro_point['gyro_y']:.2f}°/s") 
        print(f"Gyro Z: {gyro_point['gyro_z']:.2f}°/s")
```

### Supabase Edge Function

The decoder can be deployed as a Supabase Edge Function:

```bash
supabase functions deploy decoder --project-ref YOUR_PROJECT_REF
```

Send POST requests with base64-encoded BBL data:

```json
{
  "file_data": "base64_encoded_bbl_content",
  "filename": "flight_log.bbl"
}
```

## Output Format

```json
{
  "success": true,
  "frame_count": 1500,
  "headers": {
    "Product": "Betaflight",
    "Version": "4.3.0",
    "Board information": "MATEK_F405_SE"
  },
  "gyro_data": [
    {
      "timestamp": 1000,
      "gyro_x": 12.34,
      "gyro_y": -5.67,
      "gyro_z": 0.89,
      "gyro_x_raw": 202,
      "gyro_y_raw": -93,
      "gyro_z_raw": 15
    }
  ]
}
```

## Technical Details

### BBL Format Support

- **Header parsing**: Extracts firmware version, board info, and configuration
- **Field definitions**: Parses encoding and predictor information for each field
- **Frame types**: Supports I (Intra), P (Inter), S (Slow), G (GPS), H (GPS Home), E (Event)
- **Variable-length integers**: Proper signed/unsigned VB decoding
- **Predictor compression**: Implements ZERO, STRAIGHT_LINE, AVERAGE_2, INCREMENT predictors

### Gyro Data Processing

- **Raw ADC values**: Extracted from gyroADC[0], gyroADC[1], gyroADC[2] fields
- **Scaling**: Converts raw values to degrees/second using standard scale factor (1/16.4)
- **Timestamp preservation**: Maintains original timing information
- **Both raw and scaled**: Provides both processed and original values

## Testing

Run the test suite:

```bash
pytest tests/test_decoder.py -v
```

## Deployment

The decoder is designed for deployment to Supabase Edge Functions but can also be used as a standalone Python library.

## License

This implementation is based on publicly available BBL format specifications and does not include any copyrighted code from Betaflight or INAV projects.