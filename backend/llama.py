from llama_cpp import Llama

# Initialize the model
model_path = "path/to/your/model.bin"  # Replace with the path to your downloaded model
llm = Llama(model_path=model_path, n_ctx=2048)

def generate_response(prompt, max_tokens=100):
    """Generate a response from the model."""
    response = llm(prompt, max_tokens=max_tokens, echo=False)
    return response['choices'][0]['text'].strip()

# Main interaction loop
if __name__ == "__main__":
    print("Local LLM Interaction (type 'quit' to exit)")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
        
        response = generate_response(user_input)
        print(f"LLM: {response}")
