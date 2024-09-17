import gradio as gr
import time

import ollama

client = ollama.Client( "localhost:5000" )

def chat(message, history, system_prompt, vector_amount):

    messages = [{"role": "system", "content": system_prompt}]
    for question,response in history:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": response})

    messages.append({"role": "user", "content": message})

    model_name = f"Christian-Mistral-7B_{vector_amount}"

    response = client.chat(model=model_name, messages=messages)
    print(f"V: {vector_amount}\nQ: {message}\nA: {response['message']['content']}")

    return response['message']['content']

def main():
    demo = gr.ChatInterface(
        chat,
        additional_inputs=[
            gr.Textbox("You are helpful AI.", label="System Prompt"),
            gr.Slider(-2, 2, step=0.01, label="-Athiestic <----> Christian+", value=1.75),
        ],
    )

    demo.launch(share=True)

if __name__ == "__main__":
    main()
