import boto3
import json
import os
from boto3.dynamodb.types import TypeDeserializer

# Initializare
region = os.environ.get('AWS_REGION')
deserializer = TypeDeserializer()
dynamodb_resource = boto3.resource('dynamodb', region_name=region)
inventory_table = dynamodb_resource.Table('alex-inventory')

def lambda_handler(event, context):
    print(f"Primit eveniment brut: {json.dumps(event)}")
    try:
        record = event[0]
        # Acest check este o protectie suplimentara. Filtrul din Pipe este esential.
        if record.get('eventName') != 'INSERT':
            print(f"Eveniment ignorat, nu este INSERT: {record.get('eventName')}")
            return {'status': 'IGNORED', 'cause': 'Not an INSERT event'}

        new_image = record['dynamodb']['NewImage']
        # Convertim din formatul DynamoDB JSON in dictionar Python
        order_details = {k: deserializer.deserialize(v) for k, v in new_image.items()}
        print(f"Detalii comanda extrase: {json.dumps(order_details, default=str)}")
        
        order_items = order_details.get('items', [])
        if not order_items:
            return {'status': 'FAIL', 'cause': 'No items in order'}

        for item in order_items:
            item_id = item['item_id']
            required_quantity = int(item['quantity'])
            
            response = inventory_table.get_item(Key={'item_id': item_id})

            if 'Item' not in response:
                print(f"EROARE: Produsul {item_id} nu a fost gasit in inventar.")
                return {'status': 'FAIL', 'cause': f'Item {item_id} not found'}

            db_item = response['Item']
            available_stock = int(db_item['stock'])
            
            if available_stock < required_quantity:
                print(f"EROARE: Stoc insuficient pentru {item_id}. Necesar: {required_quantity}, Disponibil: {available_stock}")
                return {'status': 'FAIL', 'cause': f'Insufficient stock for {item_id}'}

        print("SUCCES: Verificare stoc finalizata.")
        # Pregatim output-ul pentru urmatoarea functie din State Machine
        return {
            "detail": order_details,
            "stock_check_status": "SUCCESS"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'FAIL', 'cause': str(e)}