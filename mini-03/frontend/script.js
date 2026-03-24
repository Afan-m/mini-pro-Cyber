const claimInput = document.getElementById('claimInput');
const urlInput = document.getElementById('urlInput');
// Image elements removed

const verifyBtn = document.getElementById('verifyBtn');
const resultsSection = document.getElementById('resultsSection');
const loader = document.getElementById('loader');
const loadingText = document.getElementById('loadingText');
const verdictBadge = document.getElementById('verdictBadge');
const reasoningText = document.getElementById('reasoningText');
const extractedTextContainer = document.getElementById('extractedTextContainer');
const extractedTextP = document.getElementById('extractedText');
const resetBtn = document.getElementById('resetBtn');


// --- Event Listeners ---

verifyBtn.addEventListener('click', startVerification);
resetBtn.addEventListener('click', resetApp);

// Add ripple effect to all buttons and interactive elements
document.querySelectorAll('.cyber-btn, .tab-btn, .chip, .reset-btn').forEach(button => {
    button.addEventListener('click', createRipple);
});

// --- Functions ---

let activeTab = 'url'; // default

function setClaim(text) {
    claimInput.value = text;
}

function switchTab(type) {
    activeTab = type;

    // UI Toggles
    document.getElementById('urlSection').classList.toggle('hidden', type !== 'url');
    document.getElementById('textSection').classList.toggle('hidden', type !== 'text');

    document.getElementById('tabUrl').classList.toggle('active', type === 'url');
    document.getElementById('tabText').classList.toggle('active', type === 'text');

    // Update Button Text (Both layers for glitch effect)
    const newText = type === 'url' ? 'ANALYZE URL' : 'ANALYZE TEXT';
    document.getElementById('btnText').innerText = newText;
    document.getElementById('btnGlitch').innerText = newText;
}

async function startVerification() {
    const text = claimInput.value.trim();
    if (!text) {
        alert("Please enter a claim.");
        return;
    }

    // Show Loader
    loader.classList.remove('hidden');
    updateLoadingText();

    // Prepare Data
    const formData = new FormData();
    if (activeTab === 'text') {
        const textValue = claimInput.value.trim();
        if (!textValue) { alert("Please enter some text content."); loader.classList.add('hidden'); return; }
        formData.append('text', textValue);
    } else {
        const urlValue = urlInput.value.trim();
        if (!urlValue) { alert("Please paste a valid URL."); loader.classList.add('hidden'); return; }
        formData.append('url', urlValue);
    }

    try {
        const response = await fetch('http://localhost:8000/api/verify', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');
        const data = await response.json();

        displayResults(data);
    } catch (error) {
        console.error(error);
        alert("Verification failed. Make sure the backend is running.");
    } finally {
        loader.classList.add('hidden');
    }
}

function updateLoadingText() {
    const steps = [
        "ESTABLISHING SECURE CONNECTION...",
        "SCANNING INPUT VECTORS...",
        "ACCESSING GLOBAL KNOWLEDGE BASE...",
        "RUNNING SEMANTIC ANALYSIS...",
        "CALCULATING VERACITY PROBABILITY...",
        "FINALIZING VERDICT..."
    ];
    let i = 0;
    const interval = setInterval(() => {
        if (loader.classList.contains('hidden')) {
            clearInterval(interval);
            return;
        }
        loadingText.innerText = steps[i % steps.length];
        i++;
    }, 800);
}

function displayResults(data) {
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });

    // Reset components for animation
    const riskBar = document.getElementById('riskBar');
    const mlBar = document.getElementById('mlBar');
    riskBar.style.width = '0%';
    mlBar.style.width = '0%';
    verdictBadge.classList.remove('show');
    verdictBadge.className = 'verdict-badge'; // reset classes

    // 1. Final Verdict Setup (but don't show yet)
    verdictBadge.innerText = data.final_verdict.toUpperCase();
    const v = data.final_verdict.toLowerCase();
    if (v === 'true' || v === 'real') verdictBadge.classList.add('badge-true');
    else if (v === 'false' || v === 'fake' || v === 'suspicious') verdictBadge.classList.add('badge-false');
    else verdictBadge.classList.add('badge-uncertain');

    // 2. Cyber Risk Stats with short delay
    const riskScore = data.analysis.cyber_risk_score;
    let riskColor = '#4ade80'; // Green
    if (riskScore > 30) riskColor = '#facc15'; // Yellow
    if (riskScore > 70) riskColor = '#ef4444'; // Red

    setTimeout(() => {
        document.getElementById('riskScore').innerText = `${riskScore}/100`;
        riskBar.style.width = `${riskScore}%`;
        riskBar.style.backgroundColor = riskColor;
        riskBar.style.color = riskColor;
    }, 50);

    // 3. ML Confidence with short delay
    const mlConf = Math.round(data.analysis.ml_confidence);
    const mlColor = '#06b6d4';

    setTimeout(() => {
        document.getElementById('mlConfidence').innerText = `${mlConf}%`;
        mlBar.style.width = `${mlConf}%`;
        document.getElementById('mlLabel').innerText = `Verdict: ${data.analysis.ml_verdict}`;
        mlBar.style.backgroundColor = mlColor;
        mlBar.style.color = mlColor;
    }, 150);

    // 4. Reveal Verdict AFTER bars finish
    setTimeout(() => {
        verdictBadge.classList.add('show');
    }, 400);

    // 5. Reasoning
    typeText(reasoningText, data.reasoning);
}

function typeText(element, text) {
    element.innerText = "";
    let i = 0;
    const speed = 20;

    function type() {
        if (i < text.length) {
            element.innerText += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

function resetApp() {
    resultsSection.classList.add('hidden');
    claimInput.value = '';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    ripple.style.width = ripple.style.height = `${diameter}px`;
    ripple.style.left = `${event.clientX - button.getBoundingClientRect().left - radius}px`;
    ripple.style.top = `${event.clientY - button.getBoundingClientRect().top - radius}px`;
    ripple.classList.add('ripple');

    const existingRipple = button.getElementsByClassName('ripple')[0];
    if (existingRipple) {
        existingRipple.remove();
    }

    button.appendChild(ripple);
}
