# Steps to run the python server 

# Create and activate a virtual environment
# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate

# On macOS/Linux:
# python3 -m venv venv
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create a .env file and add your API keys (edit with your editor of choice)
echo OPENAI_API_KEY=your_openai_key_here > .env
echo DEEPSEEK_API_KEY=your_deepseek_key_here >> .env

# Run the server
python server.py
