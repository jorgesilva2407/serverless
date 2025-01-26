import os
import requests
import redis
import importlib.util
import json
import time
import zipfile
import tempfile
import shutil

# Configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.121.187")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_INPUT_KEY     = os.getenv("REDIS_INPUT_KEY", "metrics")  # Configurable Redis input key
REDIS_OUTPUT_KEY    = os.getenv("REDIS_OUTPUT_KEY", "igorcosta-proj3-output")

POLL_INTERVAL       = int(os.getenv("REDIS_POLL_INTERVAL", 5))  # Configurable poll interval

ZIP_FILE            = os.getenv("ZIP_FILE","https://github.com/jorgesilva2407/serverless/raw/refs/heads/main/runtime/example_handler.zip")  # URL of the zip file containing function code

FUNCTION_HANDLER    = os.getenv("FUNCTION_HANDLER", "handler")  # Default entry point function name
EXTRACTION_FOLDER = "extracted_function"  # Directory to extract the ZIP contents

# Temporary directory for extracting zip files
TEMP_DIR = tempfile.mkdtemp()

class Context:
    def __init__(self, host, port, input_key, output_key):
        self.host = host
        self.port = port
        self.input_key = input_key
        self.output_key = output_key
        self.function_getmtime = None  # Timestamp of last function update
        self.last_execution = None  # Timestamp of the last function execution
        self.env = {}  # Persistent environment dictionary

def import_function_from_pyfile(file_path, function_name):
    spec = importlib.util.spec_from_file_location("usermodule", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)

def download_and_extract_zip(zip_url, extraction_path):
    """
    Downloads a ZIP file from a given URL and extracts it to the specified folder.
    """
    try:
        # Download the ZIP file
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        
        zip_file_path = "function.zip"
        with open(zip_file_path, "wb") as f:
            print("Downloading zip file")
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract the ZIP file
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            # Clear the extraction folder if it exists
            if os.path.exists(extraction_path):
                shutil.rmtree(extraction_path)
            os.makedirs(extraction_path, exist_ok=True)
            
            zip_ref.extractall(extraction_path)
        print(f"Extracted ZIP to {extraction_path}")
        
    except Exception as e:
        print(f"Error downloading or extracting ZIP: {e}")
        raise

def import_function_handler(functions_dir, handler_name):
    """
    Load all functions in Python files from the folder and return the specified handler function.
    
    Args:
        functions_dir (str): Directory containing Python files.
        handler_name (str): The name of the handler function to return.
    
    Returns:
        function: The handler function if found.
    
    Raises:
        FileNotFoundError: If the folder does not exist.
        ValueError: If the handler function is not found.
    """
    if not os.path.exists(functions_dir):
        raise FileNotFoundError(f"The folder '{functions_dir}' does not exist.")
    
    handler_function = None  # To store the target handler function

    for filename in os.listdir(functions_dir):
        if filename.endswith(".py"):
            file_path = os.path.join(functions_dir, filename)
            
            # Dynamically import the Python file
            spec = importlib.util.spec_from_file_location(filename[:-3], file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Load all functions into memory
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr):  # Check if it's a function
                    globals()[attr_name] = attr  # Load the function into global memory
            
            # Check for the specific handler function
            if hasattr(module, handler_name):
                handler_function = getattr(module, handler_name)

    if handler_function is None:
        raise ValueError(f"Handler function '{handler_name}' not found in '{functions_dir}'.")
    
    return handler_function    

def execute_function(input_,context):
    """
    Dynamically load and execute a function.
    """
    try:
        context.function_getmtime = 0 
        context.last_execution = input_["timestamp"] 

        pyfile_path = "/opt/usermodule.py"
        if os.path.exists(pyfile_path):
            print("importing from pyfile")
            func = import_function_from_pyfile(pyfile_path, "handler")
        else: 
            print("importing from zip")
            func = import_function_handler(EXTRACTION_FOLDER, FUNCTION_HANDLER)

        return func(input_,context)
    except Exception as e:
        return {"error": str(e)}

def main():
    # Initialize Redis client
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    print("Serverless runtime started. Polling for tasks...")
    print(f"Redis host: {REDIS_HOST}, port: {REDIS_PORT}, input key: {REDIS_INPUT_KEY}, poll interval: {POLL_INTERVAL}s")
    # Initialize the context variable
    context = Context(
        host =  REDIS_HOST,  # Hostname of the Redis server
        port = REDIS_PORT,  # Port of the Redis server
        input_key  = REDIS_INPUT_KEY,  # Input key for monitoring
        output_key = REDIS_OUTPUT_KEY,  # Output key for storing results
    )

    download_and_extract_zip(ZIP_FILE, EXTRACTION_FOLDER)
    while True:
        try:
            # Poll Redis for input data
            task_data = redis_client.get(REDIS_INPUT_KEY)
            if(task_data):
                task = json.loads(task_data)
                print(f"Received task:")
                # Execute the serverless function
                result = execute_function(task,context)
                print(f"Function result: {result}")

                # Store result in Redis
                redis_client.set(REDIS_OUTPUT_KEY, json.dumps(result))
            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"Runtime error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    finally:
        # Clean up temporary directory
        shutil.rmtree(TEMP_DIR)

