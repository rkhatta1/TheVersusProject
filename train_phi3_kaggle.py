import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
import os
from kaggle_secrets import UserSecretsClient

secret_label = "HF_TOKEN"
secret_value = UserSecretsClient().get_secret(secret_label)

os.environ["HF_TOKEN"] = secret_value

# --- Configuration ---
MODEL_ID = "microsoft/Phi-3-mini-4k-instruct"
TRAIN_FILE = "/kaggle/input/versus-training-data-full/train_data.jsonl"
VAL_FILE = "/kaggle/input/versus-training-data-full/val_data.jsonl"
OUTPUT_DIR = "/kaggle/working/phi3_versus_caption_lora_results_new"
NEW_MODEL_REPO_ID = "raajveerk/phi3-mini-4k-versus-caption-v1.1"

# QLoRA configuration
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# LoRA configuration
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    # These are the correct modules for Phi-3-mini
    target_modules=["qkv_proj", "o_proj", "gate_up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM",
    lora_dropout=0.05,
)

# Training Arguments
sft_config = SFTConfig(
    output_dir=OUTPUT_DIR,
    max_seq_length=1024,
    completion_only_loss=False,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    optim="paged_adamw_8bit",
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    report_to="tensorboard",
    push_to_hub=True,
    hub_model_id=NEW_MODEL_REPO_ID,
    fp16=True,
    max_steps=-1,
    do_eval=True,
    per_device_eval_batch_size=1,
    eval_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={'use_reentrant': False},
    packing=False,
)

# --- Main Fine-tuning Process ---
def run_fine_tuning():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("CUDA cache cleared.")

    print(f"Loading tokenizer from {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.padding_side = "right"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # NEW: Define the formatting function inside the main function
    # so it has access to the tokenizer
    def create_prompt(record):
        messages = [
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": record["completion"]},
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False)

    print(f"Loading model {MODEL_ID} with QLoRA configuration...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="cuda:0",
        trust_remote_code=True,
    )

    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("Loading datasets...")
    dataset = load_dataset('json', data_files={'train': TRAIN_FILE, 'validation': VAL_FILE})

    # NOTE: The manual dataset.map() step has been removed.

    print("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer, # Pass tokenizer to the trainer
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        formatting_func=create_prompt, # Use the new formatting function
        args=sft_config,
        # peft_config is not needed here as the model is already a PeftModel
    )

    print("Starting training...")
    trainer.train()
    print("Training complete!")

    final_output_path = os.path.join(OUTPUT_DIR, "final_adapters_only")
    trainer.model.save_pretrained(final_output_path)
    tokenizer.save_pretrained(final_output_path)
    print(f"LoRA adapters and tokenizer saved locally to {final_output_path}")
    print(f"Final model pushed to Hugging Face Hub: https://huggingface.co/{NEW_MODEL_REPO_ID}")

if __name__ == "__main__":
    run_fine_tuning()