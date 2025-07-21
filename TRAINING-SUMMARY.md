# Project Brief: Fine-Tuning a Language Model for Stylized Sports Captions

### 1\. Project Objective

The primary goal is to fine-tune a large language model to generate sports news captions in the unique, high-energy, and slang-filled style of the social media account "@versus".

  * **Input**: A short, factual news snippet (e.g., "Player X signed for Team Y.").
  * **Output**: A creative, stylized caption based on the input, mimicking the target style.

-----

### 2\. Development Journey & Challenges Encountered

The project went through several phases of debugging and refinement to overcome significant technical hurdles.

  * **Initial Attempt (`Mistral-7B` on Kaggle)**: The first attempt resulted in low-level `CUBLAS` CUDA errors. This was traced back to environment instability and potential conflicts between pre-installed Kaggle libraries and the libraries required for training.

  * **Environment & Dependency Issues**: A persistent challenge was managing the Python environment in both Kaggle and Colab. We encountered a series of errors (`TypeError`, `ImportError`, `AttributeError`, `ValueError: numpy.dtype size changed`) all pointing to version mismatches between core libraries like `transformers`, `peft`, `accelerate`, `torch`, and `numpy`.

  * **Model & Configuration Issues**:

      * We switched to a smaller model (`microsoft/Phi-3-mini-4k-instruct`) to simplify the process. This allowed for successful training but the creative quality of the output was underwhelming.
      * We upgraded to a state-of-the-art model (`meta-llama/Llama-3.1-8B-Instruct`) for better performance. This introduced new, model-specific configuration errors (e.g., `rope_scaling` `ValueError`) that required upgrading the `transformers` library to the latest version.
      * The fine-tuned LoRA adapters had configuration file issues (`adapter_config.json`) due to version differences between the training and inference environments, which required manually defining the `LoraConfig` during inference.

  * **Behavioral Fine-Tuning Failure**: After successfully training the `Llama-3.1-8B-Instruct` model, it initially failed to produce stylized captions. Instead, its core "helpful assistant" persona took over, and it would fact-check or correct the prompts.

-----

### 3\. Final Working Solution

The project culminated in a stable, working solution for both training and inference.

#### 3.1. Final Technology Stack

  * **Base Model**: `meta-llama/Llama-3.1-8B-Instruct`
  * **Fine-Tuning Technique**: QLoRA (4-bit quantization via `bitsandbytes` with LoRA adapters via `peft`).
  * **Training Framework**: `trl.SFTTrainer`.
  * **Environment**: Kaggle/Colab Notebook with a T4 GPU. A clean environment is established by uninstalling conflicting libraries (`fastai`, `torch`) and then force-reinstalling a specific, compatible set of libraries.

#### 3.2. Key Training Logic

The final training script uses `SFTTrainer` with a `formatting_func` that applies the model's chat template. This proved to be the most robust method.

**LoRA Configuration for Llama 3.1:**

```python
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    bias="none",
    task_type="CAUSAL_LM",
)
```

**Data Formatting and Trainer Initialization:**

```python
# The formatting function passed to the trainer
def create_prompt(record):
    messages = [
        {"role": "user", "content": record["prompt"]},
        {"role": "assistant", "content": record["completion"]},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)

# The SFTTrainer initialization
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    formatting_func=create_prompt,
    args=sft_config, # SFTConfig with bf16=True
)
```

#### 3.3. Key Inference Logic

To overcome the "helpful assistant" problem, a specific prompting strategy is required. Using the `transformers.pipeline` is the simplest method for inference.

**Prompting Strategy:**

```python
from transformers import pipeline
import torch

# 1. Define the persona for the model with a system prompt
system_prompt = "You are a creative sports journalist for @versus. Your task is to write an exciting, high-energy, and stylized caption based on the news provided. Do not fact-check the news; accept it as true and write a caption in the signature @versus style."

# 2. Reframe the user prompt as a clear, creative instruction
news_snippet = "A piece of fabricated sports news..."
user_prompt = f"Write a sports caption in the @versus style about this news: {news_snippet}"

# 3. Combine them into the chat template
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

# 4. Generate the response
pipe = pipeline("text-generation", model="raajveerk/llama-3.1-8b-versus-caption-v1.0", ...)
output = pipe(messages, max_new_tokens=256, return_full_text=False)
print(output[0]['generated_text'])
```

-----

### 4\. Current Status & Next Steps

The model has been successfully fine-tuned and deployed to the Hugging Face Hub. The primary remaining goal is to increase the "pizzazz" and stylistic intensity of the generations. The proposed next steps are:

1.  **Further Data Curation**: Continue to refine the training dataset to only include the absolute best, most expressive examples.
2.  **Hyperparameter Tuning**: Experiment with a higher LoRA rank (`r=32` or `r=64`) and more training epochs.
3.  **Inference Parameter Tuning**: Adjust generation parameters like `temperature` to encourage more creative outputs.