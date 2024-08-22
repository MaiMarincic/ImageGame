import streamlit as st
import time
import requests

# Set page config to include the game name in the tab title and use your logo as the favicon
st.set_page_config(page_title="PromptGen", page_icon="Images/icon.svg")

# Initialize session state for tracking current screen and name if not already present
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'name_input'

# Define a function to advance to the next screen
def next_screen():
    if st.session_state['current_screen'] == 'name_input':
        st.session_state['current_screen'] = 'game_rules'
        print("NS - game rules")
    elif st.session_state['current_screen'] == 'game_rules':
        st.session_state['current_screen'] = 'loading'
        print("NS - loading")
    elif st.session_state['current_screen'] == 'loading':
        st.session_state['current_screen'] = 'image_display'
        print("NS - image display")

# Define a function to handle the transition from the name input screen
def set_name():
    if st.session_state.name:  # Ensure name is not empty
        next_screen()
    else:
        st.warning("Please enter your name to continue.")

# Using columns to place logo and title on the same line
def header():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("Images/icon.svg", width=110)
    with col2:
        st.title("Welcome to PromptGen!")

# Screen logic
if st.session_state['current_screen'] == 'name_input':
    header()
    name = st.text_input("Please enter your name:", key="name")
    if st.button("Next", on_click=set_name):
        pass  # Button action is handled by the on_click function

elif st.session_state['current_screen'] == 'game_rules':
    header()
    st.write("""
    Compete against others by following these steps in PromptGen:

    1. **👀 Observe the Image**: Carefully examine the image provided to all players.
    
    2. **✍️ Write a Prompt**: Create a descriptive prompt that accurately represents the image.
    
    3. **🖼️ Generate Image**: Click the 'Generate' button to initiate the image creation process based on your prompt.
    
    4. **🔍 Evaluation of Images**: All players' generated images will be anonymously displayed. Judges or other players will vote on the best image.
    
    5. **🏆 Score Points**: Points are awarded based on the number of votes your generated image receives. The player with the most points at the end wins!
    """)
    if st.button("Got it! Let's start", on_click=next_screen):
        pass  # Transition is handled by the on_click  # Function to transition to the next screen

elif st.session_state['current_screen'] == 'loading':
    header()
    st.write("Loading, please wait...")
    my_bar = st.progress(0)
    start_time = time.time()

    try:
        while True:
            if time.time() - start_time > 300:
                st.error("Loading timed out. Please try again later.")
                break

            response = requests.get('http://127.0.0.1:5000/status')
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('completed', False):
                    my_bar.progress(100)
                    time.sleep(2)
                    st.session_state['current_screen'] = 'image_display'
                    st.rerun()
                    break
                progress = min(int(status_data.get('time', 0) / 10 * 100), 90)
                my_bar.progress(progress)
            else:
                st.error(f"Failed to fetch status: {response.status_code}")
                break
            time.sleep(1)
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {str(e)}")
    except ValueError as e:
        st.error(f"Error processing the response: {str(e)}")

elif st.session_state['current_screen'] == 'image_display':
    header()
    st.image("Images/AI-Ashe.png")  # Update this path as needed
    response = st.text_input("What's your response to this image?")
    if st.button("Submit"):
        st.write("You responded:", response)
