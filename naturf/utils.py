import time
import logging
import functools


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Get a logger for this utility module
logger = logging.getLogger(__name__)


def log_execution_time(func):
    """Decorator to log the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Entering: {func.__name__}...") # Use logger defined here
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.info(f"Exiting: {func.__name__} - Duration: {duration:.4f} seconds")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.error(f"FAILED: {func.__name__} - Duration: {duration:.4f} seconds - Error: {e}", exc_info=True)
            raise e
    return wrapper
