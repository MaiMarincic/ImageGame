from PIL import Image
import base64
from io import BytesIO

def generate_image(prompt: str) -> str:
    img = Image.open("../rawr.jpg")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def generate_prompt() -> str:
    return "prompt"
