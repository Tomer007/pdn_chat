#!/usr/bin/env python3
"""
Test class for PDN Calculator Algorithm
Tests the PDN calculator with different answer paths and validates results
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.pdn_calculator import calculate_pdn_code
from utils.report_generator import load_pdn_report


class PDNCalculatorTester:
    """
    Test class for PDN Calculator Algorithm
    """
    
    def __init__(self, answers_path: str = None):
        """
        Initialize the PDN Calculator Tester
        
        Args:
            answers_path: Path to directory containing answer files
        """
        self.answers_path = Path(answers_path) if answers_path else Path("saved_results")
        self.test_results = []
        
    def load_answers_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load answers from a JSON file
        
        Args:
            file_path: Path to the JSON file containing answers
            
        Returns:
            Dictionary containing the answers
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading answers from {file_path}: {e}")
            return {}
    
    def test_single_answer_file(self, file_path: str) -> Dict[str, Any]:
        """
        Test PDN calculation with a single answer file
        
        Args:
            file_path: Path to the answer file
            
        Returns:
            Dictionary containing test results
        """
        print(f"\n🔍 Testing file: {file_path}")
        
        # Load answers
        answers = self.load_answers_from_file(file_path)
        if not answers:
            return {"file": file_path, "status": "failed", "error": "Could not load answers"}
        
        # Extract metadata
        metadata = answers.get('metadata', {})
        user_email = metadata.get('email', 'unknown')
        user_name = f"{metadata.get('first_name', '')} {metadata.get('last_name', '')}".strip()
        
        print(f"   User: {user_name} ({user_email})")
        
        # Calculate PDN code
        try:
            pdn_code = calculate_pdn_code(answers)
            print(f"   Calculated PDN Code: {pdn_code}")
            
            # Load report data
            report_data = load_pdn_report(pdn_code) if pdn_code else {}
            
            # Analyze answer patterns
            analysis = self.analyze_answers(answers)
            
            result = {
                "file": file_path,
                "user_email": user_email,
                "user_name": user_name,
                "status": "success",
                "pdn_code": pdn_code,
                "report_loaded": bool(report_data),
                "analysis": analysis
            }
            
            print(f"   ✅ Test completed successfully")
            return result
            
        except Exception as e:
            print(f"   ❌ Error calculating PDN code: {e}")
            return {
                "file": file_path,
                "user_email": user_email,
                "user_name": user_name,
                "status": "failed",
                "error": str(e)
            }
    
    def analyze_answers(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze answer patterns to understand the test case
        
        Args:
            answers: Dictionary containing user answers
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "total_questions": 0,
            "stage_a_answers": 0,  # Questions 1-26
            "stage_b_answers": 0,  # Questions 27-37
            "stage_c_answers": 0,  # Questions 38-42
            "stage_d_answers": 0,  # Questions 43-56
            "stage_e_answers": 0,  # Questions 57-59
            "trait_counts": {"A": 0, "T": 0, "P": 0, "E": 0},
            "energy_counts": {"D": 0, "S": 0, "F": 0},
            "answer_patterns": {}
        }
        
        # Count answers by stage
        for question_num in range(1, 60):
            question_key = str(question_num)
            if question_key in answers:
                analysis["total_questions"] += 1
                
                if 1 <= question_num <= 26:
                    analysis["stage_a_answers"] += 1
                    # Count trait combinations
                    answer = answers[question_key].get('selected_option_code', '')
                    if answer in ['AP', 'ET', 'AE', 'TP']:
                        if answer not in analysis["answer_patterns"]:
                            analysis["answer_patterns"][answer] = 0
                        analysis["answer_patterns"][answer] += 1
                        
                elif 27 <= question_num <= 37:
                    analysis["stage_b_answers"] += 1
                    # Count energy preferences
                    ranking = answers[question_key].get('ranking', {})
                    for energy, rank in ranking.items():
                        if energy in analysis["energy_counts"]:
                            analysis["energy_counts"][energy] += (4 - rank)  # Higher rank = more points
                            
                elif 38 <= question_num <= 42:
                    analysis["stage_c_answers"] += 1
                    
                elif 43 <= question_num <= 56:
                    analysis["stage_d_answers"] += 1
                    
                elif 57 <= question_num <= 59:
                    analysis["stage_e_answers"] += 1
        
        return analysis
    
    def test_all_answer_files(self) -> List[Dict[str, Any]]:
        """
        Test PDN calculation with all answer files in the directory
        
        Returns:
            List of test results
        """
        print(f"🧪 Testing PDN Calculator with all answer files in: {self.answers_path}")
        print("=" * 60)
        
        if not self.answers_path.exists():
            print(f"❌ Directory not found: {self.answers_path}")
            return []
        
        results = []
        answer_files = []
        
        # Find all answer files
        for user_dir in self.answers_path.iterdir():
            if user_dir.is_dir():
                for file_path in user_dir.glob("*_answers.json"):
                    answer_files.append(file_path)
        
        if not answer_files:
            print(f"❌ No answer files found in {self.answers_path}")
            return []
        
        print(f"📁 Found {len(answer_files)} answer files")
        
        # Test each file
        for file_path in answer_files:
            result = self.test_single_answer_file(str(file_path))
            results.append(result)
        
        return results
    
    def test_specific_scenarios(self) -> List[Dict[str, Any]]:
        """
        Test specific scenarios with predefined answer patterns
        
        Returns:
            List of test results for specific scenarios
        """
        print(f"\n🧪 Testing Specific PDN Scenarios")
        print("=" * 60)
        
        scenarios = [
            {
                "name": "Pure A (Analytical) Profile",
                "description": "All answers favor Analytical trait",
                "answers": self._create_analytical_profile()
            },
            {
                "name": "Pure T (Theoretical) Profile", 
                "description": "All answers favor Theoretical trait",
                "answers": self._create_theoretical_profile()
            },
            {
                "name": "Pure P (Practical) Profile",
                "description": "All answers favor Practical trait", 
                "answers": self._create_practical_profile()
            },
            {
                "name": "Pure E (Emotional) Profile",
                "description": "All answers favor Emotional trait",
                "answers": self._create_emotional_profile()
            },
            {
                "name": "Balanced Profile",
                "description": "Even distribution across all traits",
                "answers": self._create_balanced_profile()
            }
        ]
        
        results = []
        for scenario in scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            
            try:
                pdn_code = calculate_pdn_code(scenario['answers'])
                report_data = load_pdn_report(pdn_code) if pdn_code else {}
                
                result = {
                    "scenario": scenario['name'],
                    "description": scenario['description'],
                    "status": "success",
                    "pdn_code": pdn_code,
                    "report_loaded": bool(report_data),
                    "analysis": self.analyze_answers(scenario['answers'])
                }
                
                print(f"   ✅ PDN Code: {pdn_code}")
                results.append(result)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                result = {
                    "scenario": scenario['name'],
                    "description": scenario['description'],
                    "status": "failed",
                    "error": str(e)
                }
                results.append(result)
        
        return results
    
    def _create_analytical_profile(self) -> Dict[str, Any]:
        """Create answers that favor Analytical trait"""
        answers = {"metadata": {"email": "test@example.com"}}
        
        # Stage A: All AP (Analytical + Practical)
        for i in range(1, 27):
            answers[str(i)] = {"selected_option_code": "AP"}
        
        # Stage B: All D (Dynamic) energy
        for i in range(27, 38):
            answers[str(i)] = {"ranking": {"D": 1, "S": 2, "F": 3}}
        
        # Stage C: A > T
        for i in range(38, 43):
            answers[str(i)] = {"ranking": {"A": 8, "T": 4}}
        
        # Stage D: AP > ET
        for i in range(43, 57):
            answers[str(i)] = {"ranking": {"AP": 8, "ET": 4}}
        
        # Stage E: A first
        for i in range(57, 60):
            answers[str(i)] = {"ranking": {"A": 1, "T": 2, "P": 3, "E": 4}}
        
        return answers
    
    def _create_theoretical_profile(self) -> Dict[str, Any]:
        """Create answers that favor Theoretical trait"""
        answers = {"metadata": {"email": "test@example.com"}}
        
        # Stage A: All TP (Theoretical + Practical)
        for i in range(1, 27):
            answers[str(i)] = {"selected_option_code": "TP"}
        
        # Stage B: All S (Stable) energy
        for i in range(27, 38):
            answers[str(i)] = {"ranking": {"S": 1, "D": 2, "F": 3}}
        
        # Stage C: T > A
        for i in range(38, 43):
            answers[str(i)] = {"ranking": {"T": 8, "A": 4}}
        
        # Stage D: TP > AE
        for i in range(43, 57):
            answers[str(i)] = {"ranking": {"TP": 8, "AE": 4}}
        
        # Stage E: T first
        for i in range(57, 60):
            answers[str(i)] = {"ranking": {"T": 1, "A": 2, "P": 3, "E": 4}}
        
        return answers
    
    def _create_practical_profile(self) -> Dict[str, Any]:
        """Create answers that favor Practical trait"""
        answers = {"metadata": {"email": "test@example.com"}}
        
        # Stage A: Mix of AP and TP
        for i in range(1, 14):
            answers[str(i)] = {"selected_option_code": "AP"}
        for i in range(14, 27):
            answers[str(i)] = {"selected_option_code": "TP"}
        
        # Stage B: All F (Flexible) energy
        for i in range(27, 38):
            answers[str(i)] = {"ranking": {"F": 1, "S": 2, "D": 3}}
        
        # Stage C: P > E
        for i in range(38, 43):
            answers[str(i)] = {"ranking": {"P": 8, "E": 4}}
        
        # Stage D: AP > ET
        for i in range(43, 57):
            answers[str(i)] = {"ranking": {"AP": 8, "ET": 4}}
        
        # Stage E: P first
        for i in range(57, 60):
            answers[str(i)] = {"ranking": {"P": 1, "A": 2, "T": 3, "E": 4}}
        
        return answers
    
    def _create_emotional_profile(self) -> Dict[str, Any]:
        """Create answers that favor Emotional trait"""
        answers = {"metadata": {"email": "test@example.com"}}
        
        # Stage A: All AE (Analytical + Emotional)
        for i in range(1, 27):
            answers[str(i)] = {"selected_option_code": "AE"}
        
        # Stage B: All F (Flexible) energy
        for i in range(27, 38):
            answers[str(i)] = {"ranking": {"F": 1, "D": 2, "S": 3}}
        
        # Stage C: E > P
        for i in range(38, 43):
            answers[str(i)] = {"ranking": {"E": 8, "P": 4}}
        
        # Stage D: AE > TP
        for i in range(43, 57):
            answers[str(i)] = {"ranking": {"AE": 8, "TP": 4}}
        
        # Stage E: E first
        for i in range(57, 60):
            answers[str(i)] = {"ranking": {"E": 1, "A": 2, "T": 3, "P": 4}}
        
        return answers
    
    def _create_balanced_profile(self) -> Dict[str, Any]:
        """Create answers with balanced distribution"""
        answers = {"metadata": {"email": "test@example.com"}}
        
        # Stage A: Even distribution
        patterns = ["AP", "ET", "AE", "TP"]
        for i in range(1, 27):
            answers[str(i)] = {"selected_option_code": patterns[i % 4]}
        
        # Stage B: Balanced energy
        energies = [{"D": 1, "S": 2, "F": 3}, {"S": 1, "F": 2, "D": 3}, {"F": 1, "D": 2, "S": 3}]
        for i in range(27, 38):
            answers[str(i)] = {"ranking": energies[i % 3]}
        
        # Stage C: Alternating preferences
        for i in range(38, 43):
            if i % 2 == 0:
                answers[str(i)] = {"ranking": {"A": 8, "T": 4}}
            else:
                answers[str(i)] = {"ranking": {"P": 8, "E": 4}}
        
        # Stage D: Alternating combinations
        for i in range(43, 57):
            if i % 2 == 0:
                answers[str(i)] = {"ranking": {"AP": 8, "ET": 4}}
            else:
                answers[str(i)] = {"ranking": {"AE": 8, "TP": 4}}
        
        # Stage E: Rotating preferences
        for i in range(57, 60):
            if i == 57:
                answers[str(i)] = {"ranking": {"A": 1, "T": 2, "P": 3, "E": 4}}
            elif i == 58:
                answers[str(i)] = {"ranking": {"T": 1, "P": 2, "E": 3, "A": 4}}
            else:
                answers[str(i)] = {"ranking": {"P": 1, "E": 2, "A": 3, "T": 4}}
        
        return answers
    
    def generate_test_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive test report
        
        Args:
            results: List of test results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("📊 PDN Calculator Test Report")
        report.append("=" * 60)
        
        # Summary statistics
        total_tests = len(results)
        successful_tests = len([r for r in results if r.get('status') == 'success'])
        failed_tests = total_tests - successful_tests
        
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Successful: {successful_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        report.append("")
        
        # PDN Code distribution
        pdn_codes = [r.get('pdn_code') for r in results if r.get('status') == 'success' and r.get('pdn_code')]
        if pdn_codes:
            code_counts = {}
            for code in pdn_codes:
                code_counts[code] = code_counts.get(code, 0) + 1
            
            report.append("PDN Code Distribution:")
            for code, count in sorted(code_counts.items()):
                report.append(f"  {code}: {count} ({count/len(pdn_codes)*100:.1f}%)")
            report.append("")
        
        # Detailed results
        report.append("Detailed Results:")
        report.append("-" * 40)
        
        for i, result in enumerate(results, 1):
            if result.get('status') == 'success':
                report.append(f"{i}. ✅ {result.get('scenario', result.get('user_name', 'Unknown'))}")
                report.append(f"   PDN Code: {result.get('pdn_code', 'N/A')}")
                if result.get('analysis'):
                    analysis = result['analysis']
                    report.append(f"   Questions: {analysis.get('total_questions', 0)}")
                    report.append(f"   Stages: A({analysis.get('stage_a_answers', 0)}) B({analysis.get('stage_b_answers', 0)}) C({analysis.get('stage_c_answers', 0)}) D({analysis.get('stage_d_answers', 0)}) E({analysis.get('stage_e_answers', 0)})")
            else:
                report.append(f"{i}. ❌ {result.get('scenario', result.get('user_name', 'Unknown'))}")
                report.append(f"   Error: {result.get('error', 'Unknown error')}")
            report.append("")
        
        return "\n".join(report)
    
    def run_comprehensive_test(self) -> None:
        """
        Run comprehensive test suite
        """
        print("🧪 PDN Calculator Comprehensive Test Suite")
        print("=" * 60)
        
        all_results = []
        
        # Test real answer files
        print("\n📁 Testing Real Answer Files...")
        real_results = self.test_all_answer_files()
        all_results.extend(real_results)
        
        # Test specific scenarios
        print("\n🎯 Testing Specific Scenarios...")
        scenario_results = self.test_specific_scenarios()
        all_results.extend(scenario_results)
        
        # Generate and display report
        print("\n" + "=" * 60)
        report = self.generate_test_report(all_results)
        print(report)
        
        # Save report to file
        report_file = Path("pdn_calculator_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Test report saved to: {report_file}")


def main():
    """Main function to run the PDN Calculator tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test PDN Calculator Algorithm')
    parser.add_argument('--answers-path', type=str, default='saved_results',
                       help='Path to directory containing answer files')
    parser.add_argument('--file', type=str, 
                       help='Test specific answer file')
    parser.add_argument('--scenarios-only', action='store_true',
                       help='Run only scenario tests')
    
    args = parser.parse_args()
    
    tester = PDNCalculatorTester(args.answers_path)
    
    if args.file:
        # Test specific file
        result = tester.test_single_answer_file(args.file)
        print(tester.generate_test_report([result]))
    elif args.scenarios_only:
        # Test only scenarios
        results = tester.test_specific_scenarios()
        print(tester.generate_test_report(results))
    else:
        # Run comprehensive test
        tester.run_comprehensive_test()


if __name__ == "__main__":
    main() 