import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import joblib
import os

# --- 1. Synthetic Dataset (LIAR / FakeNewsNet Style) ---
# In a real production scenario, load this from a CSV file.
data = [
    # REAL NEWS (Label 1)
    ("NASA confirms water on Mars surface", 1),
    ("World Health Organization declares global health emergency", 1),
    ("Oil prices drop as production increases", 1),
    ("Scientists discover new species of deep sea fish", 1),
    ("Government announces new tax cuts for small businesses", 1),
    ("Local elections to be held next month", 1),
    ("Study shows exercise improves mental health", 1),
    ("Tech giant releases new smartphone model", 1),
    ("Stock market reaches all-time high", 1),
    ("Average global temperature rising according to climate report", 1),
    ("New bridge construction completed ahead of schedule", 1),
    ("University researchers publish breakthrough in cancer treatment", 1),
    ("Olympics opening ceremony draws millions of viewers", 1),
    ("Electric car sales surpass traditional vehicles in Nordic region", 1),
    ("Prime Minister meets with foreign delegates", 1),
    # FAKE NEWS / CLICKBAIT / SENSATIONAL (Label 0)
    ("You won't believe what this celebrity did! SHOCKING!", 0),
    ("Doctors hate this simple trick to lose weight overnight!", 0),
    ("Aliens found in New York City sewer system!", 0),
    ("The government is controlling your mind with 5G towers!", 0),
    ("Click here to claim your free iPhone 15 Pro Max!", 0),
    ("Secret cure for cancer hidden by big pharma revealed!", 0),
    ("Earth will explode tomorrow says top scientist!", 0),
    ("Vampire bat attacks causing zombie outbreak in Florida!", 0),
    ("Drink this magic potion to live forever!", 0),
    ("Send this message to 10 friends or bad luck will follow!", 0),
    ("Millionaire reveals secret to get rich doing nothing!", 0),
    ("Shark found swimming in local swimming pool!", 0),
    ("Politician admits to being a lizard person on live TV!", 0),
    ("Scientists prove the moon is actually a hologram!", 0),
    ("Miracle food cures all diseases instantly!", 0)
]

def train_model():
    print("Initializing Machine Learning Training Pipeline...")
    
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['text', 'label'])
    
    X = df['text']
    y = df['label']
    
    # --- 2. Create Pipeline (TF-IDF + Logistic Regression) ---
    # TfidfVectorizer: Converts text to numerical vectors based on word importance.
    # LogisticRegression: A classic, interpretable binary classifier.
    model = make_pipeline(
        TfidfVectorizer(stop_words='english', max_features=1000),
        LogisticRegression(solver='liblinear')
    )
    
    # --- 3. Train Model ---
    print(f"Training on {len(data)} examples...")
    model.fit(X, y)
    
    # --- 4. Evaluate (Simple Check) ---
    test_sentences = [
        "President announces budget plan",
        "WWOOOW!! YOU WON A MILLION DOLLARS CLICK HERE!!!"
    ]
    print("\n--- Model Verification ---")
    for sent in test_sentences:
        pred = model.predict([sent])[0]
        prob = model.predict_proba([sent])[0].max()
        label = "REAL" if pred == 1 else "FAKE"
        print(f"Text: '{sent}' -> Prediction: {label} (Confidence: {prob:.2f})")
        
    # --- 5. Save Model ---
    if not os.path.exists('ml_models'):
        os.makedirs('ml_models')
        
    joblib.dump(model, 'ml_models/fake_news_classifier.pkl')
    print("\n[SUCCESS] Model saved to 'backend/ml_models/fake_news_classifier.pkl'")

if __name__ == "__main__":
    train_model()
