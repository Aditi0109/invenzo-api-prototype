import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Initialize components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_title(title: str) -> str:
    """
    Applies lowercasing, tokenization, stop word removal, 
    lemmatization, and strips special characters.
    """
    if not title or not isinstance(title, str):
        return ""
    
    # Lowercase text
    text = title.lower()
    
    # Strip special characters and keep only alphanumeric values/spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stop words and lemmatize tokens
    cleaned_tokens = [
        lemmatizer.lemmatize(token) 
        for token in tokens 
        if token not in stop_words
    ]
    
    # Join with clean spaces
    return " ".join(cleaned_tokens).strip()