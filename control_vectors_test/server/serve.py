from flask import Flask, request, jsonify
import json
import torch, os
torch.cuda.empty_cache()
from repeng import ControlVector, ControlModel, DatasetEntry
from transformers import AutoModelForCausalLM, AutoTokenizer

cpu = False

with open( "keys.json", "rt" ) as fin:
    keys = json.load( fin )

os.environ["HF_TOKEN"] = keys['hf_token']

model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)
model = model.to("cuda:0" if not cpu and torch.cuda.is_available() else "mps:0" if torch.backends.mps.is_available() else "cpu")
model = ControlModel(model, list(range(-5, -18, -1)))

christian_vector = ControlVector.import_gguf( "christian_vector_3.gguf" )


app = Flask(__name__)

@app.route( '/api/chat', methods=['POST'] )
def chat():
    data = request.json
    messages = data.get("messages", [])

    model_name = data.get("model")

    if "_" in model_name:
        vector_amount = float(model_name.split( '_' )[-1])
    else:
        vector_amount = float(model_name.split( '-' )[-1])


    # Get the tokenized tensor using apply_chat_template
    input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)

    # Create an attention mask where each token has an attention value of 1 (since all tokens are important)
    attention_mask = torch.ones(input_ids.shape, dtype=torch.long).to(model.device)

    # Create a dictionary to match the output of tokenizer()
    tokenized_output = {
        "input_ids": input_ids,
        "attention_mask": attention_mask
    }

    # Now you can use tokenized_output in the model

    max_new_tokens = 1000
    repetition_penalty = 1.1

    settings = {
        "pad_token_id": tokenizer.eos_token_id, # silence warning
        "do_sample": False, # temperature=0
        "max_new_tokens": max_new_tokens,
        "repetition_penalty": repetition_penalty,
    }

    model.set_control(christian_vector, vector_amount)

    tokens_out = model.generate(**tokenized_output, **settings ).squeeze()
    message_out = tokenizer.decode(tokens_out)

    #remove <s> and </s>
    message_out = message_out.replace("<s>", "").replace("</s>", "")
    #remove [INST] and [/INST] and everything between
    
    closing_inst_location = message_out.find("[/INST]")
    while closing_inst_location != -1:
        message_out = message_out[closing_inst_location+len("[/INST]"):].strip()
        closing_inst_location = message_out.find("[/INST]")
    

    return jsonify( {"message": {"content": message_out}} )


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)
