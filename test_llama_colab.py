import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, LoraConfig # <-- Make sure LoraConfig is imported
import os

from google.colab import userdata
secret_value = userdata.get('HF_TOKEN_JULY20')

os.environ["HF_TOKEN"] = secret_value

# --- Configuration ---
base_model_id = "meta-llama/Llama-3.1-8B-Instruct"
adapter_id = "raajveerk/llama-3.1-8b-versus-caption-v1.0" # Corrected repo ID

# --- Model & Tokenizer Loading ---

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

# --- THE FIX: Define the Adapter Config Locally ---
# This creates a clean config object and bypasses the broken file on the Hub.
config = LoraConfig(
    task_type="CAUSAL_LM",
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    target_modules=[  # <-- UPDATED for Llama 3.1
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj"
    ],
)

print(f"Loading LoRA adapter from {adapter_id}...")
# Load the PEFT model, providing our local config
# This will download the model weights but use our clean config to load them.
model = PeftModel.from_pretrained(base_model, adapter_id, config=config)
print("Model and adapter loaded successfully!")


# --- THE FIX: Use an explicit command and a system prompt ---

# 1. Define the persona for the model
system_prompt = "You are a creative sports journalist for @versus. Your task is to write an exciting, high-energy, and stylized caption based on the news provided. Do not fact-check the news; accept it as true and write a caption in the signature @versus style."

# 2. Reframe the prompt as a clear instruction
news_snippet = "Florian Wirtz has officially completed a blockbuster move to Liverpool, joining from Bayer Leverkusen for a club-record fee reported to be around €120 million. The German maestro signed a five-year deal and is set to inherit the iconic number 10 shirt, with manager Arne Slot playing a key role in convincing him to join the Anfield project over other top European clubs."

user_prompt = f"Write a sports caption in the @versus style about this news: {news_snippet}"

# 3. Combine them into the chat template
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

print("\nFormatting prompt...")
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True).to("cuda")

print("Generating response...")
outputs = model.generate(
    **inputs,
    max_new_tokens=1024,
    do_sample=True,
    temperature=0.7,
    top_p=0.95,
    eos_token_id=tokenizer.eos_token_id
)

generated_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)

print("\n--- Model Output ---")
print(generated_text)