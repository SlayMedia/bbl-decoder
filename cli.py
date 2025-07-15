"""
Command-line interface for BBL decoder
"""

import sys
import json
from decoder import decode_bbl_file

def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <bbl_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print(f"Decoding BBL file: {file_path}")
    result = decode_bbl_file(file_path)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    print(f"Successfully decoded {result['frame_count']} frames")
    print(f"Extracted {len(result['gyro_data'])} gyro data points")
    
    # Print first few gyro data points
    if result['gyro_data']:
        print("\nFirst 5 gyro data points:")
        for i, data in enumerate(result['gyro_data'][:5]):
            print(f"  {i+1}: X={data['gyro_x']:.2f}°/s, Y={data['gyro_y']:.2f}°/s, Z={data['gyro_z']:.2f}°/s")
    
    # Print headers
    if result['headers']:
        print("\nHeaders:")
        for key, value in result['headers'].items():
            print(f"  {key}: {value}")
    
    # Save detailed results to JSON
    output_file = file_path.replace('.bbl', '_decoded.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()