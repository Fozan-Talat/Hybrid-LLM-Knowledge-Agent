from langdetect import detect, DetectorFactory

# Make detection deterministic
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"
