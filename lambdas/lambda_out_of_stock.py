import boto3
import json
import os

# Adresele de email hardcodate
SENDER_EMAIL = "flalex216@gmail.com"
RECEIVER_EMAIL = "malosmihai1@gmail.com"

# Inițializează clienții AWS
region = os.environ.get('AWS_REGION')
dynamodb = boto3.resource('dynamodb', region_name=region)
ses_client = boto3.client('ses', region_name=region)

orders_table = dynamodb.Table('alex-orders')

def lambda_handler(event, context):
    """
    Gestionează eșecul verificării stocului.
    Actualizează DB și trimite un email de notificare.
    """
    print(f"Notificare eșec stoc pentru eveniment: {json.dumps(event)}")

    # Preluăm datele din evenimentul de intrare
    # Rezultatul de la check-stock-lambda este în event['Payload'] datorită ResultPath
    failure_payload = event.get('Payload', {})
    failure_cause = failure_payload.get('cause', 'Motiv necunoscut')
    
    # ID-ul comenzii este în obiectul original, la 'detail'
    order_id = event.get('detail', {}).get('order_id')

    if not order_id:
        print("EROARE: ID-ul comenzii lipsește. Nu se poate continua.")
        return {"status": "error", "cause": "Missing order_id"}

    # Pas 1: Actualizăm statusul comenzii în baza de date
    try:
        orders_table.update_item(
            Key={'order_id': order_id},
            UpdateExpression="SET order_status = :status, failure_reason = :reason",
            ExpressionAttributeValues={
                ':status': 'CANCELLED_NO_STOCK',
                ':reason': failure_cause
            }
        )
        print(f"Statusul comenzii {order_id} a fost actualizat la CANCELLED_NO_STOCK.")
    except Exception as e:
        print(f"EROARE la actualizarea statusului pentru comanda {order_id}: {e}")
        # Continuăm pentru a trimite email-ul chiar dacă actualizarea eșuează

    # Pas 2: Trimitem email-ul de notificare
    send_stock_failure_email(order_id, failure_cause)
    
    # Returnăm payload-ul original de eroare pentru ca State Machine să-l poată pasa
    # mai departe la starea de 'Fail'.
    return failure_payload


def send_stock_failure_email(order_id, reason):
    """Funcție care trimite un email de eșec folosind AWS SES."""
    
    subject = f"O problemă cu comanda ta #{order_id}"
    body_text = f"""
Salut,

Ne pare foarte rău, dar a apărut o problemă la procesarea comenzii tale cu numărul {order_id}.

Motivul este: {reason}.

Din această cauză, comanda a fost anulată. Te rugăm să încerci din nou mai târziu sau să ne contactezi pentru produse alternative.

O zi bună,
Echipa ta
    """
    
    print(f"Se încearcă trimiterea email-ului de eșec către {RECEIVER_EMAIL}...")
    
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [RECEIVER_EMAIL]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Text': {'Data': body_text, 'Charset': 'UTF-8'}}
            }
        )
        print(f"Email de eșec trimis cu succes! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Nu s-a putut trimite email-ul de eșec: {e}")