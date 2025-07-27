# --- Imports ---
import os
import torch
import threading
from flask import Flask, request, jsonify
from pyngrok import ngrok
from kaggle_secrets import UserSecretsClient
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, LoraConfig

# --- Configuration & Secrets ---
print("Setting up configuration...")
hf_secret_label = "HF_TOKEN" # Make sure you have a secret named this in Kaggle
user_secrets = UserSecretsClient()
HF_TOKEN = user_secrets.get_secret(hf_secret_label)
os.environ["HF_TOKEN"] = HF_TOKEN

ngrok_secret_label = "NGROK_AUTHTOKEN"
NGROK_TOKEN = user_secrets.get_secret(ngrok_secret_label)
ngrok.set_auth_token(NGROK_TOKEN)

ngrok_domain_label = "NGROK_DOMAIN"
NGROK_DOMAIN = user_secrets.get_secret(ngrok_domain_label)

# 3. Model IDs
base_model_id = "meta-llama/Llama-3.1-8B-Instruct"
adapter_id = "raajveerk/llama-3.1-8b-versus-caption-v1.0"

# --- Model & Tokenizer Loading (Copied from your script) ---

# Configure quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Define the Adapter Config Locally
config = LoraConfig(
    task_type="CAUSAL_LM", r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

print(f"Loading LoRA adapter from {adapter_id}...")
model = PeftModel.from_pretrained(base_model, adapter_id, config=config)
print("✅ Model and adapter loaded successfully!")


# --- Flask Web Server Definition ---
app = Flask(__name__)

@app.route("/generate-caption", methods=['POST'])
def generate_caption_route():
    # Get the news summary from the incoming request
    data = request.get_json()
    if not data or "summary" not in data:
        return jsonify({"error": "No summary provided"}), 400
    news_snippet = data["summary"]

    # Define the prompting strategy
    system_prompt = "You are a creative sports journalist for @versus. Your task is to write an exciting, high-energy, and stylized caption based on the news provided. Do not fact-check the news; accept it as true and write a caption in the signature @versus style."
    user_prompt = f"Write a sports caption in the @versus style about this news: {news_snippet}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Format the prompt and tokenize
    formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True).to("cuda")

    # Generate the response
    try:
        print(f"Generating caption for: {news_snippet[:50]}...")
        outputs = model.generate(
            **inputs,
            max_new_tokens=1536,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            eos_token_id=tokenizer.eos_token_id
        )
        generated_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        print("✅ Caption generated successfully.")
        return jsonify({"stylized_caption": generated_text.strip()})

    except Exception as e:
        print(f"🔴 ERROR during caption generation: {e}")
        return jsonify({"error": str(e)}), 500

# --- Server Startup Logic ---
def run_app():
    app.run(port=5000)

# Run Flask in a separate thread so it doesn't block the notebook
flask_thread = threading.Thread(target=run_app)
flask_thread.start()

# Serve the ngrok tunnel
final_url = ngrok.connect(5000, domain=NGROK_DOMAIN)
print("====================================================================")
print(f"✅ Your inference server is running.")
print(f"🔗 URL: {final_url}")
print("====================================================================")