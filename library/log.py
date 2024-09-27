import sys
import logging


class LogReroute(logging.Handler):
    def __init__(self, output_logger_name: str):
        super().__init__()
        self.output_logger_name = output_logger_name

    def handle(self, record: logging.LogRecord) -> bool:
        new_logger = logging.getLogger(self.output_logger_name)
        new_logger.log(record.levelno, record.getMessage())
        return True


class Log(logging.Logger):
    '''This class sets up the logging system for the application. It creates a logger object that logs 
    to a file and to the GUI. It also reroutes warnings to the log and prints ERROR messages to stderr. 
    The log level is set by the user in the settings file.
    '''
    def __init__(self, log_file: str, log_level: int, gui_logger):
        # Setup logger object
        super().__init__(name='log', level=log_level)

        # Setup status log file output
        if log_file is not None:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.addHandler(file_handler)
        
        # Set up logging to GUI
        gui_logger.setLevel(log_level)
        gui_logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.addHandler(gui_logger)
        
        # Reroute warnings to log
        logging.captureWarnings(True)
        warn_logger = logging.getLogger('py.warnings')
        warn_logger.setLevel(logging.WARNING)
        warn_logger.addHandler(LogReroute('log'))

        # Add stream handler to print ERROR messages to stderr
        err_handler = logging.StreamHandler(sys.stderr)
        err_handler.setLevel(logging.ERROR)
        self.addHandler(err_handler)
