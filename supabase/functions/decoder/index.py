"""
Supabase Edge Function for BBL Decoder
"""

import json
import base64
from decoder import decode_bbl_bytes

def handler(event, context):
    """
    Supabase Edge Function handler for BBL decoding
    
    Expected input:
    {
        "file_data": "base64_encoded_bbl_data",
        "filename": "optional_filename.bbl"
    }
    
    Returns:
    {
        "success": true/false,
        "gyro_data": [...],
        "frame_count": number,
        "headers": {...},
        "error": "error_message" (if failed)
    }
    """
    
    try:
        # Parse request body
        if hasattr(event, 'get_json'):
            body = event.get_json()
        else:
            body = json.loads(event.get('body', '{}'))
        
        if not body or 'file_data' not in body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Missing file_data in request body',
                    'success': False
                })
            }
        
        # Decode base64 data
        try:
            file_data = base64.b64decode(body['file_data'])
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': f'Invalid base64 data: {str(e)}',
                    'success': False
                })
            }
        
        # Decode BBL data
        result = decode_bbl_bytes(file_data)
        
        # Add filename if provided
        if 'filename' in body:
            result['filename'] = body['filename']
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'success': False
            })
        }

# For local testing
if __name__ == "__main__":
    # Test with sample data
    test_event = {
        'body': json.dumps({
            'file_data': base64.b64encode(b'H Product:Test\nS\nI\x64\x7F\x00').decode(),
            'filename': 'test.bbl'
        })
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))