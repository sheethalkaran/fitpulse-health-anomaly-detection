import os
import unittest
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.pdf_generator import generate_pdf_report

class TestFitPulseBasics(unittest.TestCase):
    def test_pdf_generation_basics(self):
        """Basic check to verify report PDF generation builds successfully."""
        user_id = "Test_User"
        user_details = {
            "person_id": "Test_User",
            "age": 35,
            "weight": "Normal",
            "stress": "4",
            "bp": "120/80",
            "sleep_quality": "8"
        }
        kpis = {
            "avg_hr": 72.5,
            "avg_sleep": 7.8,
            "total_steps": 12500,
            "total_anoms": 2
        }
        ai_insights = {
            "score": 88,
            "overall_status": "Healthy",
            "status_color": "green",
            "summary": "This is a basic diagnostic summary to verify ReportLab flowables, styles, and page count calculations.",
            "recommendations": [
                {
                    "metric": "Blood Pressure",
                    "status": "Good",
                    "text": "Optimal range detected.",
                    "icon": "fa-heart-pulse"
                },
                {
                    "metric": "Sleep Duration",
                    "status": "Warning",
                    "text": "Deficits on day 2. Winding down is recommended.",
                    "icon": "fa-moon"
                }
            ],
            "clinical_note": "Test disclaimer for verification purposes."
        }
        anomalies = [
            {
                "timestamp": "2026-06-06 08:00:00",
                "type": "Heart Rate",
                "hr": 145.0,
                "sleep": 7.0,
                "steps": 250
            }
        ]
        
        # Act
        pdf_path = generate_pdf_report(user_id, user_details, kpis, ai_insights, anomalies)
        
        # Assert
        self.assertTrue(os.path.exists(pdf_path), "PDF file should be created")
        self.assertTrue(os.path.getsize(pdf_path) > 0, "PDF file should not be empty")
        
        # Clean up
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass

    def test_data_preprocessing_basics(self):
        """Basic check to verify raw data preprocessing runs successfully."""
        import pandas as pd
        from module.module1_preprocessing import preprocess_data
        
        # Assemble raw data
        raw_data = {
            "Timestamp": ["2026-01-01 08:00:00", "2026-01-01 08:30:00", "2026-01-01 09:00:00"],
            "Person_ID": ["1", "1", "1"],
            "Heart_Rate": [70, 75, 80],
            "Daily_Steps": [100, 200, 300]
        }
        df_raw = pd.DataFrame(raw_data)
        
        # Preprocess
        df_clean = preprocess_data(df_raw, resample_rule="1h")
        
        # Verify resampled structure
        self.assertFalse(df_clean.empty, "Preprocessed dataframe should not be empty")
        self.assertIn("Timestamp", df_clean.columns)
        self.assertIn("Heart_Rate", df_clean.columns)


if __name__ == "__main__":
    unittest.main()
