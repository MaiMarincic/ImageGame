from PIL import Image
import base64
from io import BytesIO

def generate_image(prompt: str, func, user_id: int) -> str:
    path = "../rawr.jpg" 
    img = Image.open(path)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    func(prompt, path, user_id)
    
    return img_str

def generate_prompt() -> str:
    return "prompt"
