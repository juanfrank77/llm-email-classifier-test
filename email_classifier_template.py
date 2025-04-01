# Configuration and imports
import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Sample email dataset
sample_emails = [
    {
        "id": "001",
        "from": "angry.customer@example.com",
        "subject": "Broken product received",
        "body": "I received my order #12345 yesterday but it arrived completely damaged. This is unacceptable and I demand a refund immediately. This is the worst customer service I've experienced.",
        "timestamp": "2024-03-15T10:30:00Z"
    },
    {
        "id": "002",
        "from": "curious.shopper@example.com",
        "subject": "Question about product specifications",
        "body": "Hi, I'm interested in buying your premium package but I couldn't find information about whether it's compatible with Mac OS. Could you please clarify this? Thanks!",
        "timestamp": "2024-03-15T11:45:00Z"
    },
    {
        "id": "003",
        "from": "happy.user@example.com",
        "subject": "Amazing customer support",
        "body": "I just wanted to say thank you for the excellent support I received from Sarah on your team. She went above and beyond to help resolve my issue. Keep up the great work!",
        "timestamp": "2024-03-15T13:15:00Z"
    },
    {
        "id": "004",
        "from": "tech.user@example.com",
        "subject": "Need help with installation",
        "body": "I've been trying to install the software for the past hour but keep getting error code 5123. I've already tried restarting my computer and clearing the cache. Please help!",
        "timestamp": "2024-03-15T14:20:00Z"
    },
    {
        "id": "005",
        "from": "business.client@example.com",
        "subject": "Partnership opportunity",
        "body": "Our company is interested in exploring potential partnership opportunities with your organization. Would it be possible to schedule a call next week to discuss this further?",
        "timestamp": "2024-03-15T15:00:00Z"
    }
]


class EmailProcessor:
    def __init__(self):
        """Initialize the email processor with OpenAI API key."""
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

        # Define valid categories
        self.valid_categories = {
            "complaint", "inquiry", "feedback",
            "support_request", "other"
        }

    def validate_email(self, email: Dict) -> bool:
        """Validate a single email structure"""
        required_fields = ["id", "from", "subject", "body", "timestamp"]
        for field in required_fields:
            if field not in email:
                return False
        return True

    def classify_email(self, email: Dict) -> Optional[str]:
        """
        Classify an email using LLM.
        Returns the classification category or None if classification fails.
        
        TODO: 
        1. Design and implement the classification prompt
        2. Make the API call with appropriate error handling
        3. Validate and return the classification
        """
        prompt = f"""
        You are an expert customer service representative. Your task is to classify a given email into one of the following categories:

        - complaint: Emails that express dissatisfaction with a product or service.
        - inquiry: Questions about products and services.
        - feedback: Positive or neutral messages about products or services.
        - support_request: Requests for assistance or support.
        - other: Emails that do not fit into any of the above categories.

        Here's the email content: {email['body']}

        Please respond only with the category name from the list above. DO NOT include any additional information.
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen/qwen2.5-vl-32b-instruct:free",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = response.choices[0].message.content.strip().lower()
            # Check if the response is None or has no right attributes
            if response is None or not hasattr(response, "choices"):
                logger.error("Invalid response from the LLM API")
                return None
            
            if result in self.valid_categories:
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to classify email: {str(e)}")
            return None

    def generate_response(self, email: Dict, classification: str) -> Optional[str]:
        """
        Generate an automated response based on email classification.
        
        TODO:
        1. Design the response generation prompt
        2. Implement appropriate response templates
        3. Add error handling
        """
        response_templates = {
            "complaint": "Dear user,\n\n We apologize for the terrible experience you had with the product your received.\n\n Your issue number is {email['email_id']} One of our team members is looking into it and you will have a proper resolution in the next 24 hours.\n\n Thank you for your patience.",
            "inquiry": "Dear user,\n\n Thank you for contacting us.\n\n You will be contacted by one of our team members with a response to your question soon.\n\n Best regards.",
            "feedback": "Dear user,\n\n We appreciate the time you took to share your feedback.\n\n It help us improve our products so that we can serve you best.\n\n Thank you.",
            "support_request": "Dear user,\n\n We received your request. Your support ticket number is support-{email['email_id']} and a member of the technical team will reach out to you with a proper response to your issue.\n\n Thank you for your patience.",
            "other": "Dear user,\n\n We are processing your message and if needed you will get a response shortly.\n\n Thank you."
        }

        base_template = response_templates[classification]
        filled_template = base_template.format(email_id=email['id'])

        prompt = f"""
        You are an experienced customer support agent. Your task is to take the following email 
        response template and enhance it based on the email content and its classification.

        Email content: {email['body']}
        Classification: {classification}

        Response template: {filled_template}

        Please keep the tone of the original template and use empathetic language in the response.
        Be professional and concise (max 3-4 sentences). DO NOT add any placeholders like [NAME] or [PRODUCT]. 
        Only use information from the body of the email.
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen/qwen2.5-vl-32b-instruct:free",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")

class EmailAutomationSystem:
    def __init__(self, processor: EmailProcessor):
        """Initialize the automation system with an EmailProcessor."""
        self.processor = processor
        self.response_handlers = {
            "complaint": self._handle_complaint,
            "inquiry": self._handle_inquiry,
            "feedback": self._handle_feedback,
            "support_request": self._handle_support_request,
            "other": self._handle_other
        }

    def process_email(self, email: Dict) -> Dict:
        """
        Process a single email through the complete pipeline.
        Returns a dictionary with the processing results.
        
        TODO:
        1. Implement the complete processing pipeline
        2. Add appropriate error handling
        3. Return processing results
        """
        is_valid = self.processor.validate_email(email)
        if not is_valid:
            logger.error("Invalid email structure")
            return {
                "email_id": email['id'],
                "success": False,
                "classification": None,
                "response_sent": None
            }

        try:
            classification = self.processor.classify_email(email)
            # Check if classification is valid
            if classification not in self.response_handlers:
                logger.error(f"Invalid classification: {classification}")
                return {
                    "email_id": email['id'],
                    "success": False,
                    "classification": classification,
                    "response_sent": None
                }
            response = self.processor.generate_response(email, classification)
            result = self.response_handlers[classification](email, response)
            
            return {
                "email_id": email['id'],
                "success": True,
                "classification": classification,
                "response_sent": response
            }
        except Exception as e:
            logger.error(f"Failed to process email: {str(e)}")
            return {
                "email_id": email['id'],
                "success": False,
                "classification": None,
                "response_sent": None
            }
            

    def _handle_complaint(self, email: Dict, response: str):
        """
        Handle complaint emails.
        TODO: Implement complaint handling logic
        """
        create_urgent_ticket(email['id'], 'complaint', email['body'])
        send_complaint_response(email['id'], response)

    def _handle_inquiry(self, email: Dict, response: str):
        """
        Handle inquiry emails.
        TODO: Implement inquiry handling logic
        """
        send_standard_response(email['id'], response)

    def _handle_feedback(self, email: Dict, response: str):
        """
        Handle feedback emails.
        TODO: Implement feedback handling logic
        """
        log_customer_feedback(email['id'], email['body'])
        send_standard_response(email['id'], response)

    def _handle_support_request(self, email: Dict, response: str):
        """
        Handle support request emails.
        TODO: Implement support request handling logic
        """
        create_support_ticket(email['id'], email['body'])
        send_standard_response(email['id'], response)

    def _handle_other(self, email: Dict, response: str):
        """
        Handle other category emails.
        TODO: Implement handling logic for other categories
        """
        send_standard_response(email['id'], response)

# Mock service functions
def send_complaint_response(email_id: str, response: str):
    """Mock function to simulate sending a response to a complaint"""
    logger.info(f"Sending complaint response for email {email_id}")
    # In real implementation: integrate with email service


def send_standard_response(email_id: str, response: str):
    """Mock function to simulate sending a standard response"""
    logger.info(f"Sending standard response for email {email_id}")
    # In real implementation: integrate with email service


def create_urgent_ticket(email_id: str, category: str, context: str):
    """Mock function to simulate creating an urgent ticket"""
    logger.info(f"Creating urgent ticket for email {email_id}")
    # In real implementation: integrate with ticket system


def create_support_ticket(email_id: str, context: str):
    """Mock function to simulate creating a support ticket"""
    logger.info(f"Creating support ticket for email {email_id}")
    # In real implementation: integrate with ticket system


def log_customer_feedback(email_id: str, feedback: str):
    """Mock function to simulate logging customer feedback"""
    logger.info(f"Logging feedback for email {email_id}")
    # In real implementation: integrate with feedback system


def run_demonstration():
    """Run a demonstration of the complete system."""
    # Initialize the system
    processor = EmailProcessor()
    automation_system = EmailAutomationSystem(processor)

    # Process all sample emails
    results = []
    for email in sample_emails:
        logger.info(f"\nProcessing email {email['id']}...")
        result = automation_system.process_email(email)
        results.append(result)

    # Create a summary DataFrame
    df = pd.DataFrame(results)
    print("\nProcessing Summary:")
    print(df[["email_id", "success", "classification", "response_sent"]])

    return df


# Example usage:
if __name__ == "__main__":
    results_df = run_demonstration()
