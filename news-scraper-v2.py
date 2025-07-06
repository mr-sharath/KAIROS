import functions_framework
import requests
import firebase_admin
from firebase_admin import firestore
from datetime import datetime
import random
import os

if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()

# Get your keys from environment variables for security
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'a7847d5ecc0b4e15950387e37c31d1d6')
ANALYSIS_AGENT_URL = os.environ.get('ANALYSIS_AGENT_URL', 'https://analysis-agent-v2-684565978901.us-east1.run.app')

@functions_framework.http
def scrape_and_trigger(request):
    """
    Final definitive version. Uses NewsAPI with a dynamic query to
    ensure fresh articles and calls the analysis agent.
    """
    print("✅ Final Scraper v9 triggered.")

    # --- NEW: Dynamic query to get fresh results every time ---
    search_topics =[
    'Market Trends',
    'Financial Performance',
    'Financial Ratios',
    'Valuation',
    'Risk Analysis',
    'Investment Strategy',
    'Portfolio Management',
    'Asset Allocation',
    'Financial Modeling',
    'Discounted Cash Flow (DCF)',
    'Comparable Company Analysis',
    'Precedent Transaction Analysis',
    'Market Research',
    'Industry Analysis',
    'Capital Expenditure (CapEx)',
    'Mergers and Acquisitions (M&A)',
    'Financial Forecasting',
    'Budgeting',
    'Data Analytics',
    'Technical Analysis',
    'Fundamental Analysis'
]

    random_topic = random.choice(search_topics)
    print(f"Searching for topic: {random_topic}")

    params = {
        'apiKey': NEWS_API_KEY,
        'q': random_topic,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 5 # Smaller batch for reliability
    }
    
    try:
        response = requests.get('https://newsapi.org/v2/everything', params=params)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        if not articles:
            return f"No articles found for topic '{random_topic}'.", 200

        batch = db.batch()
        documents_to_analyze = []
        for article in articles:
            doc_id = str(hash(article.get('url') + article.get('title')))
            doc_ref = db.collection('raw_documents').document(doc_id)
            
            # --- CHANGE 1: Save the URL to raw_documents ---
            doc_data = {
                'title': article.get('title'), 
                'description': article.get('description'),
                'url': article.get('url')  # <-- We now save the URL
            }
            batch.set(doc_ref, doc_data)

            # --- CHANGE 2: Pass the URL to the analysis agent ---
            documents_to_analyze.append({
                "doc_id": doc_id,
                "text": f"Title: {doc_data['title']}\n\nDescription: {doc_data['description']}",
                "url": doc_data['url'] # <-- We now pass the URL
            })

        batch.commit()
        print(f"Saved {len(documents_to_analyze)} articles to Firestore.")

        print(f"Calling analysis-agent with {len(documents_to_analyze)} documents...")
        try:
            requests.post(ANALYSIS_AGENT_URL, json={"documents": documents_to_analyze}, timeout=15)
        except requests.exceptions.ReadTimeout:
            print("Call sent. Agent will process in background.")
        
        return "Saved articles and triggered analysis.", 200
    except Exception as e:
        return f"CRITICAL ERROR in scraper: {e}", 500
