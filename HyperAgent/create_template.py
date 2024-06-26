import os
from openai import OpenAI

API_KEY = "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"
client = OpenAI(api_key=API_KEY)

if __name__ == '__main__':
    def chatbot_response(user_input):
    # completions = openai.chat.completions.create(
    #     engine="gpt-4-turbo-preview",
    #     prompt=user_input,
    #     temperature=0.5,
    #     max_tokens=60,
    #     top_p=1.0,
    #     frequency_penalty=0.0,
    #     presence_penalty=0.0
    # )
    # return completions.choices[0].text
    completion = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"{user_input}"}
    ]
    )
    return completion.choices[0].message