def get_translation_prompt(text):
    """
    Returns a translation prompt for a given text.
    """
    return (f"translate: {text}")


def get_sentiment_analysis_prompt(text):
    """
    Returns a prompt asking the model to classify sentiment.
    """
    return f"analyze sentiment: {text}"

