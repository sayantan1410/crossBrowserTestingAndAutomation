# 1d446be994msha52d1f42edb6d91p1d2e7fjsn7933bd2094bb

import requests

def translate_to_english(text):
    API_KEY = "1d446be994msha52d1f42edb6d91p1d2e7fjsn7933bd2094bb"
    url = "https://google-translate113.p.rapidapi.com/api/v1/translator/text"

    payload = {
        "from": "auto",      # Automatically detect the input language
        "to": "en",          # Translate to English
        "text": text
    }

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": API_KEY,  # Replace with your actual key
        "X-RapidAPI-Host": "google-translate113.p.rapidapi.com"
    }

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result.get("trans")  # 'trans' key contains translated text
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Example usage
# if __name__ == "__main__":
#     API_KEY = "1d446be994msha52d1f42edb6d91p1d2e7fjsn7933bd2094bb"  # 🔐 Replace with your actual RapidAPI key
#     original_text = "El Reino Unido y Europa: no basta con ir tirando"
#     translated = translate_to_english(original_text, API_KEY)
#     if translated:
#         print("Translated:", translated)
