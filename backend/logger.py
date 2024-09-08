import logging

def setup_logger(name, log_file, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Configure AI logger
ai_logger = setup_logger("AI", 'logs/AI.log')

# Configure MainGame logger
game_logger = setup_logger("MainGame", 'logs/Game.log')

# Configure Server logger
server_logger = setup_logger("Server", 'logs/Server.log')
