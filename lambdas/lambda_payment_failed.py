import json

def lambda_handler(event, context):
    return {
        'statusCode': 404,
        'body': json.dumps('PROCESSING ERROR: Payment failed!')
    }
