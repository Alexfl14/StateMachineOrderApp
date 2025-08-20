import json
import random

def lambda_handler(event, context):
    """
    Simulează procesarea unei plăți.
    Primește evenimentul de la pasul anterior, care conține 'final_price'.
    Returnează aleatoriu 'SUCCESS' sau 'FAIL'.
    """
    print(f"Procesare plată pentru eveniment: {json.dumps(event, default=str)}")
    
    # Preluăm prețul final din starea mașinii
    final_price = event.get('final_price', 0)
    order_id = event.get('detail', {}).get('order_id', 'N/A')

    if final_price <= 0:
        print(f"Eroare plată pentru comanda {order_id}: Prețul final este invalid.")
        return {'payment_outcome': 'FAIL', 'cause': 'Invalid final price'}

    # Logica de simulare: 80% șansă de succes, 20% de eșec
    possible_outcomes = ['SUCCESS', 'SUCCESS', 'SUCCESS', 'SUCCESS', 'FAIL']
    outcome = random.choice(possible_outcomes)
    
    print(f"Comanda {order_id} cu valoarea {final_price} are rezultatul plății: {outcome}")

    # Îmbogățim evenimentul cu rezultatul plății
    event['payment_outcome'] = outcome
    
    if outcome == 'FAIL':
        # Adăugăm și o cauză pentru a fi mai explicit
        event['payment_failure_cause'] = 'Payment processor declined the transaction.'

    return event