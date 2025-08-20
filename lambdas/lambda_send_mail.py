import boto3
import json
import os
from decimal import Decimal

# Adresa de email a expeditorului, VERIFICATĂ în consola AWS SES
SENDER_EMAIL = "flalex216@gmail.com"

# Inițializează clienții AWS
region = os.environ.get('AWS_REGION')
dynamodb = boto3.resource('dynamodb', region_name=region)
ses_client = boto3.client('ses', region_name=region)

orders_table = dynamodb.Table('alex-orders')

def lambda_handler(event, context):
    """
    Finalizează o comandă, actualizează DB și trimite email la o adresă HARDCODATĂ.
    """
    print(f"Finalizare comandă pentru eveniment: {json.dumps(event, default=str)}")

    order_id = event.get('detail', {}).get('order_id')
    final_price = event.get('final_price')
    
    # --- MODIFICARE CHEIE AICI ---
    # Setăm adresa de email a destinatarului direct în cod, ignorând ce vine din eveniment.
    hardcoded_receiver_email = "malosmihai1@gmail.com"
    # ---------------------------

    if not order_id:
        raise ValueError("Eroare critică: ID-ul comenzii lipsește.")

    try:
        # Pas 1: Actualizăm statusul comenzii
        response = orders_table.update_item(
            Key={'order_id': order_id},
            UpdateExpression="SET order_status = :status, final_price = :price",
            ExpressionAttributeValues={
                ':status': 'CONFIRMED',
                ':price': Decimal(str(final_price))
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Statusul comenzii {order_id} a fost actualizat: {response}")

        # Pas 2: Trimitem email-ul de confirmare real la adresa hardcodată
        send_confirmation_email(hardcoded_receiver_email, order_id, final_price)

        return {
            'status': 'SUCCESS',
            'message': f'Comanda {order_id} a fost confirmată și email-ul a fost trimis la {hardcoded_receiver_email}.'
        }

    except Exception as e:
        print(f"A apărut o eroare la finalizarea comenzii {order_id}: {e}")
        raise e

def send_confirmation_email(to_address, order_id, price):
    """Funcție care trimite un email real folosind AWS SES."""
    
    subject = f"Confirmarea comenzii tale: #{order_id}"
    body_text = f"""
Salut,

Îți mulțumim pentru comanda ta!

Comanda cu numărul {order_id}, în valoare de {price} RON, a fost confirmată
și va fi procesată în cel mai scurt timp.

O zi bună,
Echipa ta
    """
    
    print(f"Se încearcă trimiterea email-ului către {to_address} de la {SENDER_EMAIL}...")
    
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [to_address]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Text': {'Data': body_text, 'Charset': 'UTF-8'}}
            }
        )
        print(f"Email trimis cu succes! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Nu s-a putut trimite email-ul: {e}")