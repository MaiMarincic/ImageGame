from PIL import Image
import requests
import base64
from io import BytesIO
import random
from langchain_ollama import OllamaLLM
import os
import logging
from logger import ai_logger

LOCAL_IMAGE = False
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

model = OllamaLLM(model="llama3.1")

def get_random_elements(list_of_elements, num=1):
    return random.sample(list_of_elements, min(num, len(list_of_elements)))

def generate_prompt() -> str:
    subjects = ["cat", "robot", "tree", "house", "spaceship", "monster", "superhero", "dragon", "unicorn", "mermaid", "alien", "wizard", "samurai", "cyborg", "fairy", "gargoyle", "phoenix", "centaur", "kraken", "yeti"]
    actions = ["dancing", "flying", "sleeping", "eating", "fighting", "singing", "painting", "meditating", "exploring", "transforming", "teleporting", "casting spells", "surfing", "time-traveling", "shape-shifting"]
    locations = ["on the moon", "in a forest", "underwater", "in a city", "on a mountain", "in outer space", "inside a volcano", "in a parallel universe", "on a floating island", "in a black hole", "in a crystal cave", "on a giant mushroom", "inside a computer simulation", "on a rainbow bridge", "in a steampunk airship"]
    styles = ["photorealistic", "surrealist", "cyberpunk", "art nouveau", "pixel art", "vaporwave", "baroque", "minimalist", "impressionist", "pop art", "ukiyo-e", "art deco", "gothic", "futuristic", "watercolor", "oil painting", "chalk drawing", "neon art", "glitch art", "low poly 3D"]
    additional_elements = ["with a time vortex in the background", "surrounded by floating crystals", "with fractal patterns everywhere", "in a world where gravity is reversed", "where everything is made of candy", "with portals to other dimensions", "where shadows come alive", "in a world of giant insects", "where plants have mechanical parts", "where water flows upwards"]

    base_prompt = f"A {get_random_elements(subjects)[0]} {get_random_elements(actions)[0]} {get_random_elements(locations)[0]}, {get_random_elements(styles)[0]} style"

    if random.random() > 0.5:
        base_prompt += f", {get_random_elements(additional_elements)[0]}"

    if random.random() > 0.7:
        base_prompt += f", with a {get_random_elements(subjects)[0]} {get_random_elements(actions)[0]} in the foreground"

    llm_prompt = f"Based on this description: '{base_prompt}', create a creative prompt for DALL-E to generate an image. Add specific details about colors, lighting, mood, and any other elements that would make the image unique and visually striking. The prompt should be a single paragraph, suitable for direct input into DALL-E. Feel free to add additional elements or change the description. DON'T OUTPUT ANYTHING BUT THE PROMPT! \n Prompt: \n"

    ai_logger.info(f"Prompt has been generated: {llm_prompt}")

    return llm_prompt

def get_random_elements(list_of_elements, num=1):
    return random.sample(list_of_elements, min(num, len(list_of_elements)))

def get_vector_embeddings(prompt):
    pass #TODO

def generate_image(prompt: str, insert_index, user_id: int) -> str:
    ai_logger.info(f"LOCAL_IMAGE is set to {LOCAL_IMAGE}")
    if LOCAL_IMAGE:
        img = Image.open(path)
        path = "../rawr.jpg" 
    else:
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024"
            }
        )

        ai_logger.info(response.url)
        ai_logger.info(response.json())
        ai_logger.info(response.headers)
        image_url = response.json()['data'][0]['url']
        img = Image.open(requests.get(image_url, stream=True).raw)
        path = f"Images/image_{user_id}.png"
        img.save(path)
        ai_logger.info(f"Image has been saved")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    ai_logger.info(f"Inserting into index")
    insert_index(prompt, path, user_id)
    
    return img_str

if __name__ == "__main__":
    prompt = generate_prompt()
    print(f"Generated prompt: {prompt}")
    
    def dummy_func(prompt, path, user_id):
        print(f"Image saved at {path} for user {user_id}")
    
    image_str = generate_image(prompt, dummy_func, 12345)
    print(f"Generated image string (base64): {image_str[:50]}...")
