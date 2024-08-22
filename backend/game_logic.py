import threading
from image_generation import generate_image, generate_prompt 
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass
import sqlite3
import hashlib
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GameStatus(Enum):
    SETUP = auto()
    GENERATING_INITIAL_IMAGE = auto()
    PROMPTING_PLAYERS = auto()
    GENERATING_PLAYER_IMAGES = auto()
    VOTING = auto()
    TALLYING_VOTES = auto()
    DISPLAYING_RESULTS = auto()

@dataclass
class ImgPrompt:
    prompt: str = ""
    img: Optional[str] = None

@dataclass
class Player:
    id: int
    name: str
    score: int = 0
    imgP: Optional[ImgPrompt] = None
    sendPrompt: bool = False
    vote: Optional[int] = None

class Game:
    def __init__(self, n_players: int, db_path: str):
        logger.info(f"Initializing game with {n_players} players and database at {db_path}")
        self.status: GameStatus = GameStatus.SETUP
        self.players: Dict[int, Player] = {}
        self.current_round: int = 0
        self.max_rounds: int = 5
        self.initImgPrompt: Optional[ImgPrompt] = None
        self.n_players: int = n_players
        self.votes: Dict[int, int] = {}
        self.lock = threading.Lock()
        self.db_path = db_path
        self.game_id: Optional[int] = None

    def _get_db_connection(self):
        logger.debug("Getting database connection")
        return sqlite3.connect(self.db_path)

    def ensure_game_exists(self):
        logger.info("Ensuring game exists")
        if self.game_id is None:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Game (Winner_Id) VALUES (NULL)")
                self.game_id = cursor.lastrowid
                conn.commit()
            logger.info(f"Created new game with ID: {self.game_id}")

    def add_player(self, user_id: int) -> int:
        logger.info(f"Attempting to add player with user ID: {user_id}")
        with self.lock:
            if self.status != GameStatus.SETUP:
                logger.warning(f"Cannot add players at this stage. Current status: {self.status}")
                raise ValueError("Cannot add players at this stage")
            if len(self.players) >= self.n_players:
                logger.warning("Maximum number of players reached")
                raise ValueError("Maximum number of players reached")
            
            self.ensure_game_exists()
            
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT Name FROM Users WHERE Id = ?", (user_id,))
                    result = cursor.fetchone()
                    if not result:
                        logger.warning(f"Invalid user ID: {user_id}")
                        raise ValueError("Invalid user ID")
                    
                    player_name = result[0]
                    self.players[user_id] = Player(id=user_id, name=player_name)
                    
                    cursor.execute("INSERT INTO GameParticipants (Game_Id, User_Id) VALUES (?, ?)", (self.game_id, user_id))
                    conn.commit()
                logger.info(f"Added player {player_name} (ID: {user_id}) to game {self.game_id}")
            except Exception as e:
                logger.error(f"Error adding player: {str(e)}")
                raise

            if len(self.players) == self.n_players:
                self.status = GameStatus.GENERATING_INITIAL_IMAGE
                logger.info("All players added, moving to GENERATING_INITIAL_IMAGE status")
            
            return user_id

    def login(self, username: str, password: str) -> Optional[int]:
        logger.info(f"Login attempt for user: {username}")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        hashed_password = password  # Note: This line seems to override the hashing. Consider removing if not intended.

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Id FROM Users WHERE Name = ? AND Password = ?",
                (username, hashed_password)
            )
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                logger.info(f"Successful login for user: {username} (ID: {user_id})")
                return user_id
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                return None

    def user_exists(self, user_id):
        logger.debug(f"Checking if user exists: {user_id}")
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Users WHERE Id = ?", (user_id,))
            exists = cursor.fetchone() is not None
            logger.debug(f"User {user_id} exists: {exists}")
            return exists

    def generate_initial_image(self) -> None:
        logger.info("Generating initial image")
        with self.lock:
            if self.status != GameStatus.GENERATING_INITIAL_IMAGE:
                logger.warning(f"Cannot generate initial image at this stage. Current status: {self.status}")
                raise ValueError("Cannot generate initial image at this stage")
            img = generate_image(generate_prompt())
            self.initImgPrompt = ImgPrompt("Initial prompt", img)
            self.status = GameStatus.PROMPTING_PLAYERS
            logger.info("Initial image generated, moving to PROMPTING_PLAYERS status")

    def send_prompt(self, user_id: int, player_prompt: str) -> None:
        logger.info(f"Sending prompt for user {user_id}: {player_prompt}")
        with self.lock:
            if self.status != GameStatus.PROMPTING_PLAYERS:
                logger.warning(f"Cannot send prompts at this stage. Current status: {self.status}")
                raise ValueError("Cannot send prompts at this stage")
            if user_id not in self.players:
                logger.warning(f"Invalid user ID: {user_id}")
                raise ValueError("Invalid user ID")
            player = self.players[user_id]
            player.imgP = ImgPrompt(player_prompt)
            player.sendPrompt = True
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Images (Prompt, Game_Id, User_Id) VALUES (?, ?, ?)", 
                               (player_prompt, self.game_id, user_id))
                conn.commit()
            logger.info(f"Prompt saved for user {user_id}")
            
            if self.all_prompts_sent():
                self.status = GameStatus.GENERATING_PLAYER_IMAGES
                logger.info("All prompts sent, moving to GENERATING_PLAYER_IMAGES status")

    def generate_player_images(self) -> None:
        logger.info("Generating player images")
        with self.lock:
            if self.status != GameStatus.GENERATING_PLAYER_IMAGES:
                logger.warning(f"Cannot generate player images at this stage. Current status: {self.status}")
                raise ValueError("Cannot generate player images at this stage")
            for player in self.players.values():
                if player.imgP and player.imgP.prompt:
                    img = generate_image(player.imgP.prompt)
                    player.imgP.img = img
                    logger.debug(f"Generated image for player {player.id}")
                    
                    # TODO: Generate vector embeddings for the image
                    vector_embeddings = b"placeholder_vector_embeddings"
                    
                    with self._get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO VectorIndex (Vector_embeddings, Image_Id) VALUES (?, ?)",
                                       (vector_embeddings, player.id))
                        vector_id = cursor.lastrowid
                        cursor.execute("UPDATE Images SET Vector_Id = ? WHERE Game_Id = ? AND User_Id = ?",
                                       (vector_id, self.game_id, player.id))
                        conn.commit()
                    logger.debug(f"Saved vector embeddings for player {player.id}")
            
            self.status = GameStatus.VOTING
            logger.info("All player images generated, moving to VOTING status")

    def cast_vote(self, voter_id: int, voted_for_id: int) -> bool:
        logger.info(f"Casting vote: voter {voter_id} for player {voted_for_id}")
        with self.lock:
            if self.status != GameStatus.VOTING:
                logger.warning(f"Cannot cast vote at this stage. Current status: {self.status}")
                return False
            if voter_id not in self.players or voted_for_id not in self.players:
                logger.warning(f"Invalid voter ID {voter_id} or voted_for ID {voted_for_id}")
                return False
            if voter_id == voted_for_id:
                logger.warning(f"Player {voter_id} attempted to vote for themselves")
                return False  # Players can't vote for themselves
            if self.players[voter_id].vote is not None:
                logger.warning(f"Player {voter_id} has already voted")
                return False  # Player has already voted

            self.players[voter_id].vote = voted_for_id
            self.votes[voted_for_id] = self.votes.get(voted_for_id, 0) + 1
            logger.info(f"Vote cast: {voter_id} -> {voted_for_id}")
            if self.all_votes_cast():
                self.status = GameStatus.TALLYING_VOTES
                logger.info("All votes cast, moving to TALLYING_VOTES status")
            return True

    def tally_votes(self) -> Optional[int]:
        logger.info("Tallying votes")
        with self.lock:
            if self.status != GameStatus.TALLYING_VOTES:
                logger.warning(f"Cannot tally votes at this stage. Current status: {self.status}")
                raise ValueError("Cannot tally votes at this stage")
            
            winner_id = max(self.votes, key=self.votes.get)
            winner_votes = self.votes[winner_id]

            # Check for a tie
            if list(self.votes.values()).count(winner_votes) > 1:
                logger.info("Voting resulted in a tie")
                return None  # Tie, no clear winner

            # Update scores
            for player_id, vote_count in self.votes.items():
                self.players[player_id].score += vote_count
                logger.debug(f"Updated score for player {player_id}: {self.players[player_id].score}")

            # Reset votes for next round
            self.votes.clear()
            for player in self.players.values():
                player.vote = None

            self.current_round += 1
            logger.info(f"Round {self.current_round} completed. Winner: Player {winner_id}")
            self.reset_for_next_round()
            return winner_id

    def reset_for_next_round(self) -> None:
        logger.info("Resetting for next round")
        with self.lock:
            if self.current_round >= self.max_rounds:
                self.status = GameStatus.DISPLAYING_RESULTS
                logger.info("Max rounds reached, moving to DISPLAYING_RESULTS status")
                self.end_game()
            else:
                self.status = GameStatus.GENERATING_INITIAL_IMAGE
                for player in self.players.values():
                    player.sendPrompt = False
                    player.imgP = None
                self.initImgPrompt = None
                logger.info("Reset complete, moving to GENERATING_INITIAL_IMAGE status")

    def end_game(self) -> None:
        logger.info("Ending game")
        winner_id = max(self.players.values(), key=lambda p: p.score).id
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Game SET Winner_Id = ? WHERE Id = ?", (winner_id, self.game_id))
            conn.commit()
        logger.info(f"Game ended. Winner: Player {winner_id}")

    def get_final_results(self) -> List[Dict[str, any]]:
        logger.info("Getting final results")
        with self.lock:
            results = sorted(
                [{"id": player.id, "name": player.name, "score": player.score} for player in self.players.values()],
                key=lambda x: x["score"],
                reverse=True
            )
            logger.debug(f"Final results: {results}")
            return results

    def all_prompts_sent(self) -> bool:
        all_sent = all(player.sendPrompt for player in self.players.values())
        logger.debug(f"All prompts sent: {all_sent}")
        return all_sent

    def all_votes_cast(self) -> bool:
        all_cast = all(player.vote is not None for player in self.players.values())
        logger.debug(f"All votes cast: {all_cast}")
        return all_cast

    def get_game_status(self) -> Dict[str, any]:
        with self.lock:
            status = {
                "status": self.status.name,
                "number_of_players": len(self.players),
                "current_round": self.current_round,
                "max_rounds": self.max_rounds,
            }
            logger.debug(f"Game status: {status}")
            return status

    def get_initial_image(self) -> Optional[str]:
        with self.lock:
            image = self.initImgPrompt.img if self.initImgPrompt else None
            logger.debug(f"Initial image retrieved: {'Yes' if image else 'No'}")
            return image

    def get_player_images(self) -> Dict[int, Optional[str]]:
        with self.lock:
            images = {player_id: player.imgP.img if player.imgP else None 
                      for player_id, player in self.players.items()}
            logger.debug(f"Player images retrieved: {len(images)}")
            return images
