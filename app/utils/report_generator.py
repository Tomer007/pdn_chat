import json
from pathlib import Path


def load_pdn_report(pdn_code: str) -> dict:
    """
    Load the report data for a specific PDN code from the JSON file.
    
    Args:
        pdn_code (str): The PDN code to get the report for
        
    Returns:
        dict: The report data for the specified PDN code
    """
    # Get the path to the reports JSON file
    reports_path = Path(__file__).parent.parent / "data" / "pdn_reports.json"

    try:
        # Load the JSON file
        with open(reports_path, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)

        # Get the report for the specific PDN code
        report = reports_data.get(pdn_code)

        if not report:
            # If the PDN code is not found, return the default E5 report
            return reports_data.get("E5", {})

        return report

    except Exception as e:
        print(f"Error loading report for PDN code {pdn_code}: {str(e)}")
        return {}
