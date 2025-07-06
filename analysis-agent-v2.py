import functions_framework
import firebase_admin
from firebase_admin import firestore
from gradio_client import Client

if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()

try:
    client = Client("SharathReddy/kairos")
    print("✅ Successfully connected to Hugging Face client.")
except Exception as e:
    print(f"--- ERROR: Could not connect to Hugging Face client: {e} ---")
    client = None

@functions_framework.http
def analyze_documents_http(request):
    if not client: return "HF Client not initialized.", 500

    documents = request.get_json(silent=True).get("documents", [])
    print(f"✅ Final Agent v11 TRIGGERED with {len(documents)} documents.")

    for doc in documents:
        # --- CHANGE 3: Receive the URL from the payload ---
        doc_id, article_text, source_url = doc.get("doc_id"), doc.get("text"), doc.get("url")
        try:
            print(f"Sending doc {doc_id} to AI model...")
            analysis_text = client.predict(article_text=article_text, api_name="/predict")
            
            # --- CHANGE 4: Save the URL along with the analysis ---
            db.collection('analyzed_events').document(doc_id).set({
                'original_title': article_text.split('\n')[0].replace('Title: ',''),
                'source_url': source_url, # <-- We now save the URL
                'analysis': analysis_text,
                'analyzed_at': firestore.SERVER_TIMESTAMP
            })
            print(f"✅ Success: Saved analysis and URL for {doc_id}.")

        except Exception as e:
            print(f"--- ERROR processing doc {doc_id}: {e} ---")
            
    return "Processing complete.", 200
