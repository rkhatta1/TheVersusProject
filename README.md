## The Versus Project
It's a passion project to optimize and accelerate some stuff with AI (of course), for my favourite football page on the internet: **@versus**.

### What does this repo contain?
It contains the data to finetune the microsoft phi3 model, in Kaggle notebook.

**Training Notebook Config:**
- Kaggle, P100 GPU
- Internet switched **ON**
- huggingface access token saved as **HF_TOKEN**

**Test Notebook Config:**
- Google Colab, T4 GPU
- Rest, Same as training notebook
- For some reason, the exact ```test_phi3_colab.py``` code that ran on Google Colab (T4) just would not run in Kaggle (T4 as well).

### Current Status:
**- Tested the trained llama model and it works very well. Moving on to the application part of the project.**
- Training new (cleaned and truncated) data on Meta's Llama 3.2, 8B model, because the Phi3 model did not perform well enough for us to make a product out of it.