import streamlit as st
import time
import requests
import base64
from PIL import Image
from io import BytesIO

# Set page config
st.set_page_config(page_title="PromptGen", page_icon="Images/icon.svg")

# Backend URL
BACKEND_URL = "http://127.0.0.1:5000"

# Initialize session state
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'login'
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'player_id' not in st.session_state:
    st.session_state['player_id'] = None
if 'last_status_check' not in st.session_state:
    st.session_state['last_status_check'] = 0

def header():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("Images/icon.svg", width=110)
    with col2:
        st.title("Welcome to PromptGen!")

def register_user(username, password):
    response = requests.post(f"{BACKEND_URL}/register", json={"username": username, "password": password})
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("user_id")
    return None

def login_user(username, password):
    response = requests.post(f"{BACKEND_URL}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("user_id")
    return None

def add_player(user_id):
    response = requests.post(f"{BACKEND_URL}/add_player", json={"user_id": user_id})
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("playerId")
    return None

def get_player_images():
    response = requests.get(f"{BACKEND_URL}/get_player_images")
    if response.status_code == 200:
        data = response.json()
        images = data.get("images")
        if images:
            decoded_images = {}
            for player_id, image_data in images.items():
                try:
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(BytesIO(image_bytes))
                    decoded_images[player_id] = image
                except Exception as e:
                    st.error(f"Error decoding image for player {player_id}: {str(e)}")
            return decoded_images
        else:
            st.warning("No player images received.")
    elif response.status_code == 400:
        st.warning("Player images not ready yet. Please wait.")
    else:
        st.error("Failed to load player images. Please refresh the page.")
    return None

def send_vote(voter_id, voted_for_id):
    response = requests.post(f"{BACKEND_URL}/send_vote", json={"player_id": voter_id, "voted_for_id": voted_for_id})
    if response.status_code == 200:
        return response.json()
    return None

def get_game_status():
    response = requests.get(f"{BACKEND_URL}/game_status")
    if response.status_code == 200:
        return response.json()
    return None

def get_initial_image():
    response = requests.get(f"{BACKEND_URL}/get_initial_image")
    if response.status_code == 200:
        data = response.json()
        image_data = data.get("image")
        st.error(image_data)
        if image_data:
            try:
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
                return image
            except Exception as e:
                st.error(f"Error decoding image: {str(e)}")
        else:
            st.warning("No image data received.")
    elif response.status_code == 400:
        st.warning("Initial image not ready yet. Please wait.")
    else:
        st.error("Failed to load initial image. Please refresh the page.")
    return None

def send_prompt(player_id, prompt):
    response = requests.post(f"{BACKEND_URL}/send_prompt", json={"player_id": player_id, "player_prompt": prompt})
    return response.status_code == 200

def check_and_update_game_status():
    current_time = time.time()
    if current_time - st.session_state['last_status_check'] > 2:  # Check every 2 seconds
        status = get_game_status()
        st.session_state['last_status_check'] = current_time
        if status:
            if status['status'] == 'PROMPTING_PLAYERS' and st.session_state['current_screen'] in ['waiting_for_players', 'waiting_for_generation']:
                st.session_state['current_screen'] = 'initial_image'
                st.rerun()
            elif status['status'] == 'VOTING' and st.session_state['current_screen'] in ['waiting_for_generation', 'initial_image']:
                st.session_state['current_screen'] = 'voting'
                st.rerun()
        return status
    return None

# Screen logic
if st.session_state['current_screen'] == 'login':
    header()
    st.write("Please log in or register to play.")
    
    login_username = st.text_input("Username:", key="login_username")
    login_password = st.text_input("Password:", type="password", key="login_password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login"):
            if login_username and login_password:
                user_id = login_user(login_username, login_password)

                if user_id:
                    st.session_state['user_id'] = user_id
                    player_id = add_player(user_id)
                    if player_id:
                        st.session_state['player_id'] = player_id
                        st.session_state['current_screen'] = 'waiting_for_players'
                        st.rerun()
                    else:
                        st.error("Failed to join the game. Please try again.")
                else:
                    st.error("Invalid credentials. Please try again.")
            else:
                st.warning("Please enter both username and password.")
    
    with col2:
        if st.button("Register"):
            st.session_state['current_screen'] = 'register'
            st.rerun()

elif st.session_state['current_screen'] == 'register':
    header()
    st.write("Register a new account")
    
    reg_username = st.text_input("Choose a username:", key="reg_username")
    reg_password = st.text_input("Choose a password:", type="password", key="reg_password")
    reg_confirm_password = st.text_input("Confirm password:", type="password", key="reg_confirm_password")
    
    if st.button("Register"):
        if reg_username and reg_password and reg_confirm_password:
            if reg_password == reg_confirm_password:
                user_id = register_user(reg_username, reg_password)
                if user_id:
                    st.success("Registration successful! You can now log in.")
                    st.session_state['current_screen'] = 'login'
                    st.rerun()
                else:
                    st.error("Registration failed. Please try again.")
            else:
                st.error("Passwords do not match. Please try again.")
        else:
            st.warning("Please fill in all fields.")
    
    if st.button("Back to Login"):
        st.session_state['current_screen'] = 'login'
        st.rerun()

elif st.session_state['current_screen'] == 'waiting_for_players':
    header()
    st.write("Waiting for other players to join...")
    status = check_and_update_game_status()
    if status:
        st.write(f"Current game status: {status['status']}")
        st.write(f"Number of players: {status['number_of_players']}")
    
    if st.button("Refresh Status"):
        st.rerun()

elif st.session_state['current_screen'] == 'initial_image':
    header()
    initial_image = get_initial_image()
    if initial_image:
        st.image(initial_image, caption="Initial Image", use_column_width=True)
        prompt = st.text_input("Enter your prompt based on this image:")
        if st.button("Submit Prompt"):
            if send_prompt(st.session_state['player_id'], prompt):
                st.session_state['current_screen'] = 'waiting_for_generation'
                st.rerun()
            else:
                st.error("Failed to submit prompt. Please try again.")
    else:
        st.write("Waiting for the initial image...")
    
    check_and_update_game_status()

elif st.session_state['current_screen'] == 'waiting_for_generation':
    header()
    st.write("Waiting for all players to submit prompts and generate images...")
    status = check_and_update_game_status()
    if status:
        st.write(f"Current game status: {status['status']}")
    
    if st.button("Refresh Status"):
        st.rerun()

elif st.session_state['current_screen'] == 'voting':
    header()
    player_images = get_player_images()
    if player_images:
        st.write("Vote for the best image (excluding your own):")
        cols = st.columns(len(player_images))
        for i, (player_id, image) in enumerate(player_images.items()):
            if player_id != st.session_state['player_id']:
                with cols[i]:
                    st.image(image, caption=f"Player {player_id}'s Image", use_column_width=True)
                    if st.button(f"Vote for Image {i+1}", key=f"vote_{i}"):
                        result = send_vote(st.session_state['player_id'], player_id)
                        if result:
                            if result.get("game_over"):
                                st.session_state['final_results'] = result.get("final_results")
                                st.session_state['current_screen'] = 'game_over'
                            else:
                                st.session_state['round_winner'] = result.get("round_winner")
                                st.session_state['current_screen'] = 'round_results'
                            st.rerun()
    else:
        st.warning("Waiting for player images to be generated...")

elif st.session_state['current_screen'] == 'round_results':
    header()
    st.write(f"Round Winner: Player {st.session_state['round_winner']}")
    if st.button("Start Next Round"):
        st.session_state['current_screen'] = 'waiting_for_generation'
        st.rerun()

elif st.session_state['current_screen'] == 'game_over':
    header()
    st.write("Game Over!")
    st.write("Final Results:")
    for player, score in st.session_state['final_results'].items():
        st.write(f"Player {player}: {score} points")
    if st.button("Start New Game"):
        st.session_state['current_screen'] = 'name_input'
        st.session_state['player_id'] = None
        st.rerun()

# Periodic status check
if st.session_state['current_screen'] in ['waiting_for_players', 'waiting_for_generation']:
    check_and_update_game_status()
    time.sleep(1)  # Wait for 1 second before checking again
    st.rerun()
