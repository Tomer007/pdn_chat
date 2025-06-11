import unittest
import os
from firebase_admin import firestore, credentials, initialize_app, firebase_admin
import time

from app.utils.store_pdn_report_in_Firebase import store_pdn_report_in_Firebase

class TestStorePdnReportInFirebaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize Firebase only once for all tests
        if not firebase_admin._apps:
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/Users/tomer.gur/dev-tools/pdn_chat/secrets/pdn-navigator-firebase-adminsdk-fbsvc-bfabd04cad.json')
            cred = credentials.Certificate(cred_path)
            initialize_app(cred)

    def test_store_and_verify_report(self):
        # Prepare test data
        user_metadata = {'user_id': 'test_user', 'email': 'test@example.com'}
        pdn_code = 'TESTCODE'
        report_data = {'score': 99, 'result': 'pass'}
        path = 'test/path'
        voice_path = 'test/voice/path'

        # Call the function
        doc_id = store_pdn_report_in_Firebase(user_metadata, pdn_code, report_data, path, voice_path)

        # Wait a moment for Firestore to update
        time.sleep(2)

        # Verify the document exists in Firestore
        db = firestore.client()
        docs = db.collection('pdn_reports').where('user_metadata.user_id', '==', 'test_user').stream()
        found = False
        for doc in docs:
            data = doc.to_dict()
            if data['pdn_code'] == pdn_code and data['report_data'] == report_data:
                found = True
                # Clean up: delete the test document
                db.collection('pdn_reports').document(doc.id).delete()
                break

        self.assertTrue(found, "Test PDN report was not found in Firestore.")

if __name__ == '__main__':
    unittest.main()