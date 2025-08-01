"""
Project configuration settings for diet-project.
Contains shared random state configuration for reproducible results.
"""

# Random state/seed for reproducible results across all scripts
RANDOM_STATE = 42

def get_random_state():
    """
    Get the project-wide random state/seed value.
    
    Returns:
        int: Random state/seed value for reproducible results
    """
    return RANDOM_STATE
