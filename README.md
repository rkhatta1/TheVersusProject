<div align="center">
<a href="https://www.youtube.com/watch?v=-R9WLOhUsWE">
    <img src="https://img.youtube.com/vi/-R9WLOhUsWE/maxresdefault.jpg" alt=" I trained AI to behave like my favorite football page!" width="360px">
</a>
</br>
<div style="font-size: 2.4rem; margin-bottom: 1rem; margin-top: 0.5rem"><strong>The Versus Project</strong></div>
<span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=%23ffffff&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/Vite-f3f3f3?style=flat&logo=vite&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=%23000000&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=%23ffffff&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/-20BEFF?style=flat&logo=kaggle&logoColor=%23000000&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=%23ffffff&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/Gemini-8E75B2?style=flat&logo=googlegemini&logoColor=%23ffffff&logoSize=auto"></span><span style="margin-top: 10px; width: 4rem; margin-right: 0.5rem;"><img alt="Static Badge" src="https://img.shields.io/badge/HuggingFace-040404?style=flat&logo=huggingface&logoColor=%23FFD21E&logoSize=auto"></span>
</div>

<!-- # Versus: AI-Powered Sports News Aggregator -->

## Project Overview

I love @versus, and that's why I fine-tuned an LLM on versus' captions and made an end-to-end AI content tool with it. Low-cost deployment for projects featuring local LLM's is essentially non-existent, so I decided against deployment.

## Tech Stack

*   **Backend:** Python, Flask, Flask-JWT-Extended, Flask-Bcrypt
*   **Frontend:** React (with Vite), Tailwind CSS, shadcn/ui
*   **Database:** PostgreSQL (managed with Docker Compose)
*   **AI & APIs:** Google Gemini, Instagrapi, Newspaper3k
*   **Containerization:** Docker

## Local Development Setup

### Prerequisites

*   Python>=3.10
*   Node.js and npm
*   Docker and Docker Compose
*   Kaggle account

### Step 1: Set Up the Backend

1.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create an Instagram session:**
    
-   Tip: Login to the same instagram account on your browser as well, and browse around normally, every once in a  while. This will keep your session from being tagged as "abnormal".

    ```bash
    python3 insta_login.py
    ```

### Step 2: Set Up the Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Return to the root directory:**
    ```bash
    cd ..
    ```

### Step 3: Configure Environment Variables

-   Create a `.env` file in the root of the project and add the following variables:

    ```env
    # --- Gemini API Key ---
    GEMINI=<your-gemini-api-key>

    # --- Instagram Credentials ---
    INSTA_USERNAME=<your_instagram_username>
    INSTA_PASSWORD=<your_instagram_password>

    # --- Kaggle Inference Server URL ---
    KAGGLE_INFERENCE_URL=https://your-ngrok-url.ngrok-free.app

    # --- PostgreSQL Database Credentials ---
    POSTGRES_USER=versusdb
    POSTGRES_PASSWORD=<your_secure_password>
    POSTGRES_DB=versus_db
    POSTGRES_PORT=5433

    # --- RSS Feed URL ---
    RSS_FEED=https://www.theguardian.com/football/rss

    # --- JWT Secret Key ---
    JWT_SECRET_KEY=<a_very_strong_and_secret_key>
    ```

### Step 4: Set Up the Kaggle Notebook

-   **Kaggle Config:**
    
    ```env
    T4/P100 GPU
    Enable Internet

    # -- Secretes --
    NGROK_AUTHTOKEN=<your-ngrok-auth-token>
    NGROK_DOMAIN=https://your-ngrok-url.ngrok-free.app
    HF_TOKEN=<your-huggingface-access-token>
    ```

-   **Sample Inference Server:**

    ```env
    # ---------------------------------- Cell #1 ----------------------------------
    !pip uninstall -y torch torchvision torchaudio numpy


    # ---------------------------------- Cell #2 ----------------------------------
    !pip install numpy==1.26.4


    # ---------------------------------- Cell #3 ----------------------------------
    !pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121


    # ---------------------------------- Cell #4 ----------------------------------
    !pip install --upgrade transformers peft accelerate bitsandbytes datasets trl flask pyngrok


    # ---------------------------------- Cell #5 ----------------------------------
    # Refer inference_example.py
    # Make sure to "Restart and Clear All Cell Outputs" after installing all the dependencies.
    ```

### Step 5: Start the Services

1.  **Start the PostgreSQL Database:**
*   Open a terminal in the project root and run:
    ```bash
    docker compose up -d
    ```

2.  **Start the Backend Server:**
*   In a new terminal, make sure your Python virtual environment is activated, and run the Flask application:
    ```bash
    python app_ig.py
    ```

3.  **Start the Frontend Development Server:**
*   In a third terminal, navigate to the `frontend` directory.
*   Run the Vite development server:
    ```bash
    npm run dev
    ```

