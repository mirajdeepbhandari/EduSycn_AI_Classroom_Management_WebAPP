import os
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

class SentimentAnalyzer:
    def __init__(self, MODEL_DIR):
        """
        Initialize the SentimentAnalyzer with a pretrained DistilBERT model.
        """
        try:
            # Convert Windows backslashes to forward slashes
            model_path = MODEL_DIR.replace('\\', '/')
            
            # Explicitly tell the model to load from local files
            self.tokenizer = DistilBertTokenizer.from_pretrained(
                model_path, 
                local_files_only=True
            )
            
            self.model = DistilBertForSequenceClassification.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            self.model.eval()
            
        except Exception as e:
            print(f"Detailed error: {e}")
            raise RuntimeError(f"Error loading model: {e}")

        # Define label mapping (0 -> Negative, 1 -> Positive)
        self.label_map = {0: "Negative", 1: "Positive"}

    def predict(self, text):
        """
        Predict sentiment for a single string input.

        :param text: Input text from frontend.
        :return: Dictionary with predicted label and confidence score.
        """
        if not isinstance(text, str) or text.strip() == "":
            return {"error": "Invalid input. Provide a non-empty string."}

        try:
            # Tokenize and preprocess input
            inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=512)

            # Perform inference
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Get logits and convert to probabilities
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1)

            # Get predicted class and confidence score
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence_score = probabilities[0][predicted_class].item()

            # Map predicted class to label
            sentiment_label = self.label_map[predicted_class]

            return {
                "text": text,
                "predicted_label": sentiment_label,
                "confidence_score": round(confidence_score * 100, 2)  # Convert to percentage
            }

        except Exception as e:
            return {"error": f"Prediction error: {e}"}