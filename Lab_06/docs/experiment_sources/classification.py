def classify_pages(pages):
    if pages >= 500:
        return "large"
    if pages >= 100:
        return "medium"
    return "small"
