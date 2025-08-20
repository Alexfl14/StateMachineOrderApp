import json
import boto3
import uuid
import time
import os

region = os.environ.get('AWS_REGION')
dynamodb = boto3.resource('dynamodb', region_name=region)
orders_table = dynamodb.Table('alex-orders')

def lambda_handler(event, context):
    print(f"Received API event: {json.dumps(event)}")
    try:
        # Extragem body-ul din request-ul API Gateway
        if 'body' in event:
            order_data = json.loads(event['body'])
        else:
            # Pentru testare directa
            order_data = event
        
        # Validari minime
        if 'client_details' not in order_data or 'items' not in order_data:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Lipsesc detaliile clientului sau lista de produse (items).'})}
        
        # Generam un ID unic pentru comanda
        order_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        # Cream obiectul pe care il vom insera in DynamoDB
        new_order = {
            'order_id': {"S" : order_id},
            'client_details': order_data['client_details'],
            'items': order_data['items'],
            'order_status': 'PENDING', # Statusul initial care este verificat de filtru
            'created_at': timestamp
        }

        # Inseram comanda in tabelul alex-orders
        orders_table.put_item(Item=new_order)
        
        print(f"Comanda {order_id} a fost creata cu succes in DynamoDB.")
        
        # Returnam un raspuns de succes catre client (API Gateway)
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Comanda a fost primita si este in curs de procesare.',
                'order_id': order_id
            })
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'A aparut o eroare interna: {str(e)}'})
        }