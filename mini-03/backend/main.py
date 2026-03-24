import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Local Modules
from local_verifier import verify_locally, get_model_status
from ml_engine import predict_fake_news
from ml_engine import predict_fake_news
from cyber_guard import analyze_security_risk, validate_input_quality
from gemini_learner import verify_with_gemini
from gemini_learner import verify_with_gemini

app = FastAPI(title="Claim Verification API (Local + ML + CyberSec)")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced Response Model
class DetailedAnalysis(BaseModel):
    semantic_verdict: str
    semantic_confidence: float
    ml_verdict: str
    ml_confidence: float
    cyber_risk_score: int
    cyber_details: List[str]

class VerificationResponse(BaseModel):
    final_verdict: str
    confidence: float
    reasoning: str
    analysis: DetailedAnalysis

@app.get("/api/health")
async def health_check():
    status = get_model_status()
    return {
        "service": "Claim Verification AI (Hybrid Architecture)",
        "ai_status": status,
        "modules": ["Semantic-RAG", "ML-Classifier", "Cyber-Guard"]
    }

@app.post("/api/verify", response_model=VerificationResponse)
async def verify_claim(
    request: Request,
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None)
):
    try:
        client_ip = request.client.host
        
        if not text and not url:
             return VerificationResponse(
                final_verdict="Uncertain",
                confidence=0.0,
                reasoning="Please provide either a claim text or a URL to verify.",
                analysis=DetailedAnalysis(
                    semantic_verdict="None", semantic_confidence=0,
                    ml_verdict="None", ml_confidence=0,
                    cyber_risk_score=0, cyber_details=[]
                )
            )

        # Set a default text if only URL is provided for the security check message
        if not text:
            text = f"URL verification requested for: {url}"

        # --- 0. Quality Check (Gibberish Detection) ---
        is_valid, invalid_reason = validate_input_quality(text)
        if not is_valid:
             return VerificationResponse(
                final_verdict="Invalid",
                confidence=0.0,
                reasoning=f"⚠️ {invalid_reason}",
                analysis=DetailedAnalysis(
                    semantic_verdict="Skipped", semantic_confidence=0,
                    ml_verdict="Skipped", ml_confidence=0,
                    cyber_risk_score=0, cyber_details=["Input Quality Check Failed"]
                )
            )

        # Combine Text and URL for analysis
        full_text_for_security = text
        if url:
            full_text_for_security += f" Source: {url}"

        # --- 1. Cyber Security Check ---
        security_report = analyze_security_risk(full_text_for_security, client_ip)
        risk_score = security_report["risk_score"]
        
        # If High Security Risk (DoS or Blacklist), block or flag immediately
        if risk_score >= 80:
             return VerificationResponse(
                final_verdict="SUSPICIOUS",
                confidence=100.0,
                reasoning=f"BLOCKED BY CYBER GUARD: High Security Risk detected ({risk_score}/100).",
                analysis=DetailedAnalysis(
                    semantic_verdict="Skipped", semantic_confidence=0,
                    ml_verdict="Skipped", ml_confidence=0,
                    cyber_risk_score=risk_score,
                    cyber_details=security_report["details"]
                )
            )

        # --- 2. Semantic Verification (RAG) ---
        semantic_result = verify_locally(text)
        
        # --- 3. Machine Learning Classification ---
        ml_result = predict_fake_news(text)
        
        # --- 4. Final Decision Logic (Hybrid Voting) ---
        
        final_verdict = "Uncertain"
        final_confidence = 0.0
        final_reasoning = ""
        
        sem_verdict = semantic_result['verdict']
        sem_conf = semantic_result['confidence']
        
        # LOGIC:
        # 1. Strong Local Match (>70%) -> Trust DB
        # 2. Weak Local Match (<70%) -> Try Wikipedia (Auto-Learn)
        # 3. No Wiki Match -> Fallback to ML
        
        if sem_conf > 70 and sem_verdict != "Uncertain":
            # Database Match - Trust this the most
            final_verdict = sem_verdict
            final_confidence = sem_conf
            final_reasoning = f"VERIFIED FACTION: {semantic_result['reasoning']}"
            
        else:
            # Fallback: Ask Gemini & Auto-Learn
            gemini_result = verify_with_gemini(text)
            print(f"DEBUG: Gemini result for '{text[:20]}...': {gemini_result is not None}")
            
            if gemini_result:
                 final_verdict = gemini_result['verdict']
                 final_confidence = gemini_result['confidence']
                 final_reasoning = gemini_result['reasoning']
            else:
                # Model Fallback if Gemini fails
                final_verdict = ml_result['label']
                final_confidence = ml_result['confidence']
                final_reasoning = f"AI PREDICTION: Rated as {ml_result['label'].upper()} based on linguistic patterns. {semantic_result['reasoning']}"

        # Adjust for Cyber Risk
        if risk_score > 30:
            final_reasoning += f"\n[WARNING] Security Risk detected (Score: {risk_score})."
            final_confidence = max(0, final_confidence - (risk_score * 0.2))

        return VerificationResponse(
            final_verdict=final_verdict,
            confidence=round(final_confidence, 1),
            reasoning=final_reasoning,
            analysis=DetailedAnalysis(
                semantic_verdict=sem_verdict,
                semantic_confidence=sem_conf,
                ml_verdict=ml_result['label'],
                ml_confidence=ml_result['confidence'],
                cyber_risk_score=risk_score,
                cyber_details=security_report["details"]
            )
        )

    except Exception as e:
        print(f"Error during verification: {e}")
        # Return fallback error
        return VerificationResponse(
            final_verdict="Uncertain",
            confidence=0.0,
            reasoning=f"Internal System Error: {str(e)}",
            analysis=DetailedAnalysis(
                semantic_verdict="Error", semantic_confidence=0,
                ml_verdict="Error", ml_confidence=0,
                cyber_risk_score=0, cyber_details=[str(e)]
            )
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
