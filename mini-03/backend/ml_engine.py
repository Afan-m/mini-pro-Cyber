import joblib
import os
import numpy as np

MODEL_PATH = 'ml_models/fake_news_classifier.pkl'
_model = None

def load_ml_model():
    global _model
    if _model is not None:
        return _model
        
    if not os.path.exists(MODEL_PATH):
        print(f"Warning: ML Model not found at {MODEL_PATH}. Run train_ml.py first.")
        return None
        
    try:
        print("Loading ML Classifier...")
        _model = joblib.load(MODEL_PATH)
        print("ML Classifier loaded successfully.")
        return _model
    except Exception as e:
        print(f"Error loading ML model: {e}")
        return None

def predict_fake_news(text):
    """
    Predicts if the text is Real information or Fake/Clickbait using the ML model.
    Returns:
        dict: { 'label': 'Real'/'Fake', 'confidence': float (0-100) }
    """
    model = load_ml_model()
    
    if model is None:
        return {
            "label": "Unknown",
            "confidence": 0.0,
            "error": "Model not loaded"
        }
        
    try:
        # Predict class (0=Fake, 1=Real)
        prediction_class = model.predict([text])[0]
        # Predict probabilities [prob_fake, prob_real]
        probabilities = model.predict_proba([text])[0]
        
        # Get the probability of the predicted class
        confidence_score = probabilities[prediction_class] * 100
        
        label_str = "Real" if prediction_class == 1 else "Fake"
        
        return {
            "label": label_str,
            "confidence": round(confidence_score, 2),
            "probabilities": {
                "real": round(probabilities[1] * 100, 2),
                "fake": round(probabilities[0] * 100, 2)
            }
        }
    except Exception as e:
        print(f"Prediction Error: {e}")
        return {
            "label": "Error",
            "confidence": 0.0
        }
