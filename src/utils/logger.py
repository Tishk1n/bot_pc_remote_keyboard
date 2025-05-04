import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create file handler which logs even debug messages
    fh = logging.FileHandler('anime_voice_assistant.log')
    fh.setLevel(logging.DEBUG)
    
    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add the handlers to the logger if not already added
    if not logger.hasHandlers():
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

logger = setup_logger('AnimeVoiceAssistant')

def log(message, level="info"):
    if level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)
    else:
        logger.info(message)

# Example usage
logger.debug('Debugging information')
logger.info('Information message')
logger.warning('Warning message')
logger.error('Error message')
logger.critical('Critical message')