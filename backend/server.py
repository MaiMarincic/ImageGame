import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from game_logic import Game, GameStatus
import traceback
from logger import server_logger

app = Flask(__name__)
CORS(app)
NUMBER_OF_PLAYERS = 3
DB_PATH = "Database/game_database.db"
game = Game(NUMBER_OF_PLAYERS, DB_PATH)

# Verbose logging flag
VERBOSE = False

@app.before_request
def log_request_info():
    server_logger.debug('Request:')
    server_logger.debug('Headers: %s', request.headers)
    server_logger.debug('Body: %s', request.get_data())
    server_logger.debug('-'*10)

@app.after_request
def log_response_info(response):
    server_logger.debug('Response:')
    server_logger.debug('Response status: %s', response.status)
    server_logger.debug('Response headers: %s', response.headers)
    server_logger.debug('-'*10)
    return response

def verbose_log(message):
    if VERBOSE:
        server_logger.debug(message)

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
        
        user_id = game.register_user(username, password)
        return jsonify({"success": True, "user_id": user_id})
    except Exception as e:
        server_logger.error(f"Error in register: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        server_logger.info(f"Login attempt for user: {username}")
        
        if not username or not password:
            server_logger.warning("Missing username or password in login attempt")
            return jsonify({"error": "Missing username or password"}), 400
        
        user_id = game.login(username, password)
        if user_id:
            server_logger.info(f"Successful login for user: {username} with ID: {user_id}")
            return jsonify({"success": True, "user_id": user_id})
        else:
            server_logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        server_logger.error(f"Error in login: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/add_player', methods=['POST'])
def add_player():
    try:
        server_logger.info("Received add_player request")
        data = request.json
        user_id = data.get('user_id')
        
        server_logger.info(f"Attempting to add player with user ID: {user_id}")
        
        if not user_id:
            server_logger.warning("Attempt to add player without user_id")
            return jsonify({"error": "Missing user_id"}), 400
        
        player_id = game.add_player(user_id)
        server_logger.info(f"Successfully added player with ID: {player_id}")
        
        if game.status == GameStatus.GENERATING_INITIAL_IMAGE:
            server_logger.info("Starting initial image generation")
            try:
                game.generate_initial_image()
            except Exception as e:
                server_logger.error(f"Error generating initial image: {str(e)}")
                return jsonify({"error": "Failed to generate initial image"+ str(e)}), 500
        
        return jsonify({"success": True, "playerId": player_id})
    except ValueError as ve:
        server_logger.warning(f"ValueError in add_player: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        server_logger.error(f"Unexpected error in add_player: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

# The rest of the routes (get_initial_image, send_prompt, game_status, get_player_images, send_vote) 
# remain mostly the same, but you should update them to check for user authentication:

@app.route('/get_initial_image', methods=['GET'])
def get_initial_image():
    try:
        if game.status != GameStatus.PROMPTING_PLAYERS:
            return jsonify({"error": "Initial image not ready yet"}), 400
        img = game.get_initial_image()
        server_logger.info("Initial image retrieved")
        verbose_log(f"Retrieved initial image: {img[:100]}...")  # Log first 100 chars of image data
        return jsonify({"image": img})
    except Exception as e:
        server_logger.error(f"Error in get_initial_image: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/send_prompt', methods=['POST'])
def send_prompt():
    try:
        data = request.json
        player_id = data.get('player_id')
        player_prompt = data.get('player_prompt')
        
        if not player_prompt:
            server_logger.error("Missing player_prompt in request")
            return jsonify({"error": "Missing player_prompt"}), 400
        
        game.send_prompt(player_id, player_prompt)
        server_logger.info(f"Player {player_id} sent prompt: {player_prompt}")
        
        if game.status == GameStatus.GENERATING_PLAYER_IMAGES:
            threading.Thread(target=game.generate_player_images).start()
        
        return jsonify({"success": True})
    except ValueError as ve:
        server_logger.warning(str(ve))
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        server_logger.error(f"Error in send_prompt: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/game_status', methods=['GET'])
def game_status():
    try:
        status = game.get_game_status()
        server_logger.info(f"Game status requested: {status}")
        return jsonify(status)
    except Exception as e:
        server_logger.error(f"Error in game_status: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/get_player_images', methods=['GET'])
def get_player_images():
    try:
        if game.status != GameStatus.VOTING:
            return jsonify({"error": "Player images not ready yet"}), 400
        images = game.get_player_images()
        server_logger.info("Player images retrieved")
        verbose_log(f"Retrieved player images: {len(images)} images")
        return jsonify({"images": images})
    except Exception as e:
        server_logger.error(f"Error in get_player_images: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/send_vote', methods=['POST'])
def send_vote():
    try:
        data = request.json
        user_id = data.get('user_id')
        voted_for_id = data.get('voted_for_id')
        
        if not voted_for_id:
            server_logger.error("Missing voted_for_id in request")
            return jsonify({"error": "Missing voted_for_id"}), 400
        
        server_logger.info(f"Player {user_id} voted for Player {voted_for_id}")
        
        if game.status == GameStatus.TALLYING_VOTES:
            round_winner = game.tally_votes()
            
            if round_winner is None:
                server_logger.info("No clear winner this round (likely a tie)")
                return jsonify({"tie": True})
            
            server_logger.info(f"Round winner: Player {round_winner}")
            
            if game.status == GameStatus.DISPLAYING_RESULTS:
                final_results = game.get_final_results()
                server_logger.info("Game over. Final results: " + str(final_results))
                return jsonify({"game_over": True, "final_results": final_results})
            else:
                return jsonify({"game_over": False, "round_winner": round_winner})
        
        return jsonify({"success": True})
    except Exception as e:
        server_logger.error(f"Error in send_vote: {str(e)}")
        server_logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({"success": True})

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    if args.verbose:
        VERBOSE = True
        server_logger.setLevel(logging.DEBUG)
        server_logger.info("Verbose logging enabled")
    
    app.run(debug=True)
