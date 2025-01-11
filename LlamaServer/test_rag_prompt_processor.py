import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import the process_prompt function from the main script
from rag_prompt_processor import process_prompt  # Replace "main_script" with the actual filename of your main script

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
        user_prompt = input("\nEnter your prompt (or type 'exit' to quit): ").strip()
        
        # Exit condition
        if user_prompt.lower() == "exit":
            logging.info("Exiting the test script. Goodbye!")
            break
        
        # Process the user's prompt
        if user_prompt:  # Ensure the prompt is not empty
            test_process_prompt(user_prompt)
        else:
            logging.warning("Please enter a valid prompt.")
