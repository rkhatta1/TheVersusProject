import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, LoraConfig # <-- Make sure LoraConfig is imported
import os

from google.colab import userdata
secret_value = userdata.get('HF_TOKEN')

os.environ["HF_TOKEN"] = secret_value

# --- Configuration ---
base_model_id = "microsoft/Phi-3-mini-4k-instruct"
adapter_id = "raajveerk/phi3-mini-4k-versus-caption-v1.1" # Corrected repo ID

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
    target_modules=[
        "o_proj",
        "qkv_proj",
        "gate_up_proj",
        "down_proj"
    ],
)

print(f"Loading LoRA adapter from {adapter_id}...")
# Load the PEFT model, providing our local config
# This will download the model weights but use our clean config to load them.
model = PeftModel.from_pretrained(base_model, adapter_id, config=config)
print("Model and adapter loaded successfully!")


# --- Inference ---
prompt_text = "Marcus Rashford signed for FC Barcelona, as Nico Williams rejected the club's offer last month. Rashford had shown keen interest in playing for the club as early as January of this year."
messages = [{"role": "user", "content": prompt_text}]

print("\nFormatting prompt...")
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True).to("cuda")

print("Generating response...")
outputs = model.generate(
    **inputs,
    max_new_tokens=1024,
    do_sample=True,
    temperature=0.85,
    repetition_penalty=1.1,
    top_p=0.95,
    eos_token_id=tokenizer.eos_token_id
)

generated_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)

print("\n--- Model Output ---")
print(generated_text)