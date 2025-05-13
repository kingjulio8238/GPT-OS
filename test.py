import mlx.core as mx
import subprocess
import shlex
import os
import sys
from mlx_lm.utils import load
from mlx_lm import generate
import mlx.core as mx
from PIL import Image
import base64
from io import BytesIO
import time
import re
import requests
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# response = generate(model, tokenizer, temp=0.7, max_tokens=500, prompt="write me a poem about the ocean", verbose=True)

"""
INSERT YOUR OPENAI API KEY IN THE GPT4O FUNCTION!!
"""


stop_words = ["<|im_start|>", "<|im_end|>", "<s>", "</s>"]


def multimodal_generate(image_path, combined_prompt):
    model = "mlx-community/llava-phi-3-mini-4bit"
    prompt = combined_prompt
    max_tokens = 100
    temperature = 0.0

    image_arg = f'"{image_path}"' if os.path.isfile(image_path) else f'"{image_path}"'
    command = f"""
    python3 -m mlx_vlm.generate --model {model} \
    --prompt "{prompt}" --image {image_arg} \
    --max-tokens {max_tokens} --temp {temperature}
    """
    args = shlex.split(command)
    result = subprocess.run(args, capture_output=True, text=True)

    return (
        result.stdout.strip()
        if result.returncode == 0
        else "Error in image description"
    )


def generate_response(model_name, combined_prompt):
    if "gemma" in model_name.lower():
        model, tokenizer = load("mlx-community/quantized-gemma-2b-it")
    else:
        model, tokenizer = load("mlx-community/Phi-3-mini-4k-instruct-4bit")

    start_time = time.time()  # Start timing
    
    # Use the generate function from mlx_lm
    response = generate(
        model=model,
        tokenizer=tokenizer,
        prompt=combined_prompt,
        max_tokens=500,
        temp=0.7,
        stop_words=stop_words,
        verbose=False
    )
    
    end_time = time.time()  # End timing
    tokens = tokenizer.encode(response)
    tokens_per_second = len(tokens) / (end_time - start_time)  # Calculate tokens per second
    
    yield response, tokens_per_second


def print_chunks(text):
    # Process the chunk to ensure it ends with a period
    last_period = text.rfind(".")  # Find the last period in the text
    if last_period != -1:  # If a period is found
        return text[: last_period + 1]  # Return the text up to the last period
    else:
        return text  # If no period found, return the whole chunk


def master_generate(model, prompt):
    response = ""
    tok_speed = 0
    num_chunks = 0
    for chunk, speed in generate_response(model, prompt):
        num_chunks += 1
        tok_speed += speed
        chunk = print_chunks(chunk)
        chunk = re.sub(r"^/\*+/", "", chunk)
        chunk = re.sub(r"^:+", "", chunk)
        chunk = chunk.replace("", "")
        chunk = chunk.replace("<|end|><|assistant|>", "")
        print(chunk)
        response += chunk

    tok_speed /= num_chunks

    # Perform text processing
    junk = []
    response = re.sub(r"^/\*+/", "", response)
    response = re.sub(r"^:+", "", response)
    response = response.replace("", "")
    response = response.replace("<|end|><|assistant|>", "")
    print("$!$" + model)
    print("^@^" + str(tok_speed))


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def gpt4o_response(text, image_path):
    try:
        # Getting the base64 string
        base64_image = encode_image(image_path)
        api_key = os.environ.get("OPENAI_API_KEY", "INSERT YOUR API KEY")
        
        # Check if API key is set
        if api_key == "INSERT YOUR API KEY" or not api_key:
            error_msg = "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable."
            print(error_msg)
            print("$!$openai")
            print("^@^0")
            return
            
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        t = time.time()
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            "max_tokens": 200,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )
        t_end = time.time()
        
        # Check if the response is successful
        response.raise_for_status()
        out = response.json()
        
        # Check if the expected keys exist in the response
        if "choices" not in out or len(out["choices"]) == 0:
            error_msg = f"Unexpected API response format: {out}"
            print(error_msg)
            print("$!$openai")
            print("^@^0")
            return
            
        output = out["choices"][0]["message"]["content"]
        tok_speed = len(output.split(" ")) / (t_end - t)
        model = "openai"
        print(output)
        print("$!$" + model)
        print("^@^" + str(tok_speed))
        
    except requests.exceptions.RequestException as e:
        error_msg = f"API request error: {str(e)}"
        print(error_msg)
        print("$!$openai")
        print("^@^0")
        
    except KeyError as e:
        error_msg = f"API response missing expected keys: {str(e)}\nResponse: {out if 'out' in locals() else 'No response data'}"
        print(error_msg)
        print("$!$openai")
        print("^@^0")
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        print("$!$openai")
        print("^@^0")


def ollama_response(text, image_path):
    try:
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "model": "llava:13b",
            "prompt": text,
            "images": [base64_image],
            "stream": False,
        }

        response = requests.post(
            "http://localhost:11434/api/generate", headers=headers, json=payload
        )
        
        response.raise_for_status()
        json_response = response.json()
        
        if "response" not in json_response:
            error_msg = f"Unexpected API response format: {json_response}"
            print(error_msg)
            print("$!$ollama")
            print("^@^0")
            return
            
        output = json_response["response"]
        
        if "eval_count" in json_response and "eval_duration" in json_response:
            tok_speed = json_response["eval_count"] / json_response["eval_duration"] * 10**9
        else:
            tok_speed = 0

        print(output)
        print("$!$ollama")
        print("^@^" + str(tok_speed))
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API request error: {str(e)}"
        print(error_msg)
        print("$!$ollama")
        print("^@^0")
        
    except Exception as e:
        error_msg = f"Unexpected error in Ollama response: {str(e)}"
        print(error_msg)
        print("$!$ollama")
        print("^@^0")


def extract_text(input_text):
    # This regex looks for any content between double quotes, ensuring that it ignores all text before "== Prompt"
    match = re.search(r'== Prompt:[^"]*"([^"]*)"', input_text)
    if match:
        return match.group(1)
    else:
        return "No matching text found."


def process_data(model, text, image_data_url):
    # Decode the image from data URL
    local = False
    if "openai" not in model:
        local = True

    if local:
        # Generate description of the image
        if "phi" in model:
            """
            header, encoded = image_data_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(BytesIO(image_data))
            image.save("temp_image.png")  # Save the image temporarily
            """
            combined_prompt = f"You are a helpful desktop assistant. We've also provided some context from the user's screen. Now answer the user's question: {text}"
            t_o = time.time()
            output = multimodal_generate(
                tempfile.gettempdir() + "/screenshot.png", combined_prompt
            )
            lst = output.split("<|assistant|>")
            lst2 = lst[1].split("==")
            output = lst2[0]
            t_end = time.time()
            tok_speed = len(output.split(" ")) / (t_end - t_o)
            print(output)
            print("$!$" + model)
            print("^@^" + str(tok_speed))
        elif "ollama" in model:
            combined_prompt = f"You are a helpful desktop assistant. We've also provided some context from the user's screen. Now answer the user's question: {text}"
            response = ollama_response(
                combined_prompt, tempfile.gettempdir() + "/screenshot.png"
            )
        else:  # gemma
            combined_prompt = f"You are a helpful desktop assistant. Now answer the user's question: {text}"
            response = master_generate(model, combined_prompt)

    else:
        try:
            # Try using OpenAI's GPT-4o first
            combined_prompt = f"You are a helpful desktop assistant. We've also provided some context from the user's screen. Now answer the user's question: {text}"
            response = gpt4o_response(
                combined_prompt, tempfile.gettempdir() + "/screenshot.png"
            )
            
            # If response is None or an error occurred in gpt4o_response
            if "API" in str(response) or "error" in str(response).lower():
                raise Exception("OpenAI API error, falling back to Phi model")
                
        except Exception as e:
            print(f"Falling back to Phi model due to: {str(e)}")
            # Fall back to using Phi model
            combined_prompt = f"You are a helpful desktop assistant. We've also provided some context from the user's screen. Now answer the user's question: {text}"
            t_o = time.time()
            output = multimodal_generate(
                tempfile.gettempdir() + "/screenshot.png", combined_prompt
            )
            lst = output.split("<|assistant|>")
            lst2 = lst[1].split("==")
            output = lst2[0]
            t_end = time.time()
            tok_speed = len(output.split(" ")) / (t_end - t_o)
            print(output)
            print("$!$phi")  # Use phi instead of openai since we're falling back
            print("^@^" + str(tok_speed))

    # Clean up temporary image file
    # os.remove("temp_image.png") # why tf is this here

    # return response


info = sys.argv[1]
datum = info.split("$!$")
model = datum[0]
prompt = datum[1]
image_data_url = sys.argv[2]
model = model.lower()
output = process_data(model, prompt, image_data_url)
