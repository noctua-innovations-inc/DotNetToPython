import logging
import os
import sys

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import the process_prompt function from the main script
from rag_prompt_processor import process_prompt

def test_process_prompt(prompt):
    """
    Test the process_prompt function directly.
    """
    try:
        logging.info(f"Processing prompt: {prompt}")
        response = process_prompt(prompt)
        logging.info(f"Response: {response}")
    except Exception as e:
        logging.error(f"Error during prompt processing: {e}")


if __name__ == "__main__":
    # Interactive prompt loop
    while True:
        # Get user input
        user_query = input("\nEnter your prompt (or type 'exit' to quit): ").strip()
        
        # Exit condition
        if user_query.lower() == "exit":
            logging.info("Exiting the test script. Goodbye!")
            break
        
        # Process the user's prompt
        if user_query:  # Ensure the prompt is not empty
            test_process_prompt(user_query)
        else:
            logging.warning("Please enter a valid prompt.")
