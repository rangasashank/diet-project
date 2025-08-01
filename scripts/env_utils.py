"""
Shared utility functions for the diet-project scripts.
Handles environment variable access for dataset paths.
"""

import os

def get_dataset_path():
    """
    Get the project root path using DATASETDIRPATH environment variable.
    DATASETDIRPATH points to notebooks/datasets, so we need to go up two levels to get project root.
    
    Returns:
        str: Project root directory path
    """
    try:
        # Get DATASETDIRPATH from environment variable (set by conda environment)
        dataset_path = os.getenv('DATASETDIRPATH')
        
        if dataset_path:
            # DATASETDIRPATH points to notebooks/datasets, we need project root
            # Go up two levels: notebooks/datasets -> notebooks -> project_root
            project_root = os.path.dirname(os.path.dirname(dataset_path))
            print(f"Using project root from DATASETDIRPATH: {project_root}")
            return project_root
        else:
            # Fallback: try to determine project root relative to script location
            # Assume this module is in scripts/ directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            print(f"DATASETDIRPATH not found, using relative path: {project_root}")
            return project_root
        
    except Exception as e:
        print(f"Warning: Could not determine project path: {e}")
        # Final fallback to current working directory
        return os.getcwd()
