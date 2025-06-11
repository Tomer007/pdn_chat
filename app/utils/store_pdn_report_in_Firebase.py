from firebase_admin import firestore, credentials, initialize_app
import logging
from datetime import datetime
import os
import firebase_admin
from firebase_admin import credentials




logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        # Check if Firebase is already initialized
        try:
            firestore.client()
            logger.info("Firebase already initialized")
            return True
        except ValueError:
            pass
        
        # Initialize Firebase with service account key
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/Users/tomer.gur/dev-tools/pdn_chat/secrets/pdn-navigator-firebase-adminsdk-fbsvc-bfabd04cad.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        return False

def store_pdn_report_in_Firebase(user_metadata: dict, pdn_code: str, report_data: dict, path: str, voice_path: str):
    """
    Save the report data to the Firebase Firestore database.
    
    Args:
        user_metadata (dict): Dictionary containing user's metadata
        pdn_code (str): The PDN code identifier
        report_data (dict): The processed report data to be saved
        path (str): The path to the report in the Firebase Firestore database
        voice_path (str): The path to the voice recording in the Firebase Firestore database

        
    Returns:
        str: Document ID of the saved report
        
    Raises:
        Exception: If saving to Firestore fails
    """
    try:
        # Initialize Firebase if not already done
        if not initialize_firebase():
            raise Exception("Failed to initialize Firebase")
        
        db = firestore.client()
        
        report_doc = {
            'user_metadata': user_metadata,
            'pdn_code': pdn_code,
            'report_data': report_data,
            'report_path': path,
            'voice_path': voice_path,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'completed'
        }
        
        doc_ref = db.collection('pdn_reports').add(report_doc)
        document_id = doc_ref[1].id
        
        logger.info(f"PDN report saved with ID: {document_id}")
        return document_id
        
    except Exception as e:
        logger.error(f"Failed to save PDN report: {str(e)}")
        raise Exception(f"Failed to save PDN report: {str(e)}")