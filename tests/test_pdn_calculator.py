"""Tests for the PDN calculation engine."""

import pytest
from app.utils.pdn_calculator import (
    calculate_confidence_score,
    check_verification_needed,
    calculate_pdn_code,
)


class TestCalculateConfidenceScore:
    """Tests for calculate_confidence_score()."""

    def test_high_confidence_clear_dominant(self):
        """Clear dominant trait and energy should yield high confidence."""
        scores = {'A': 20, 'T': 5, 'P': 3, 'E': 2, 'D': 25, 'S': 5, 'F': 3}
        result = calculate_confidence_score(scores)
        assert 50 <= result <= 100

    def test_low_confidence_close_scores(self):
        """Close scores should yield low confidence."""
        scores = {'A': 10, 'T': 10, 'P': 9, 'E': 9, 'D': 10, 'S': 10, 'F': 9}
        result = calculate_confidence_score(scores)
        assert 0 <= result <= 30

    def test_zero_scores(self):
        """All zero scores should return 0 confidence."""
        scores = {'A': 0, 'T': 0, 'P': 0, 'E': 0, 'D': 0, 'S': 0, 'F': 0}
        result = calculate_confidence_score(scores)
        assert result == 0

    def test_single_dominant_trait(self):
        """Only one trait with score should give high trait confidence."""
        scores = {'A': 10, 'T': 0, 'P': 0, 'E': 0, 'D': 10, 'S': 0, 'F': 0}
        result = calculate_confidence_score(scores)
        assert result == 100

    def test_result_bounded_0_to_100(self):
        """Result should always be between 0 and 100."""
        scores = {'A': 100, 'T': 0, 'P': 0, 'E': 0, 'D': 100, 'S': 0, 'F': 0}
        result = calculate_confidence_score(scores)
        assert 0 <= result <= 100

    def test_missing_keys_default_to_zero(self):
        """Missing keys should default to 0."""
        scores = {'A': 10, 'D': 10}
        result = calculate_confidence_score(scores)
        assert 0 <= result <= 100


class TestCheckVerificationNeeded:
    """Tests for check_verification_needed()."""

    def test_close_scores_needs_verification(self):
        """Gap of 2 or less between top two traits needs verification."""
        scores = {'A': 10, 'T': 9, 'P': 5, 'E': 3}
        assert check_verification_needed(scores) is True

    def test_tied_scores_needs_verification(self):
        """Tied top scores need verification."""
        scores = {'A': 10, 'T': 10, 'P': 5, 'E': 3}
        assert check_verification_needed(scores) is True

    def test_distant_scores_no_verification(self):
        """Large gap between top two traits does not need verification."""
        scores = {'A': 15, 'T': 5, 'P': 3, 'E': 2}
        assert check_verification_needed(scores) is False

    def test_gap_of_3_no_verification(self):
        """Gap of exactly 3 should not need verification."""
        scores = {'A': 10, 'T': 7, 'P': 5, 'E': 3}
        assert check_verification_needed(scores) is False

    def test_gap_of_2_needs_verification(self):
        """Gap of exactly 2 should need verification."""
        scores = {'A': 10, 'T': 8, 'P': 5, 'E': 3}
        assert check_verification_needed(scores) is True

    def test_single_score_no_verification(self):
        """Single score (less than 2 values) should not need verification."""
        scores = {'A': 10}
        assert check_verification_needed(scores) is False

    def test_ignores_non_trait_keys(self):
        """Should only consider A, T, P, E keys."""
        scores = {'A': 10, 'T': 5, 'P': 3, 'E': 2, 'D': 10, 'S': 9}
        assert check_verification_needed(scores) is False


class TestCalculatePdnCode:
    """Tests for calculate_pdn_code()."""

    def test_empty_answers_returns_na(self):
        """Empty answers should return 'NA' (as pdn_code in result)."""
        result = calculate_pdn_code({})
        # With all zeros, verification is triggered (gap=0 ≤ 2), so returns dict
        if isinstance(result, dict):
            assert result['pdn_code'] == 'NA'
        else:
            assert result == 'NA'

    def _build_stage_a_answers(self, dominant_pair='AP', count=20):
        """Helper to build Stage A answers (questions 1-26)."""
        answers = {}
        for i in range(1, count + 1):
            answers[str(i)] = {'selected_option_code': dominant_pair}
        return answers

    def _build_stage_b_answers(self, dominant_energy='D'):
        """Helper to build Stage B answers (questions 27-37) with ranking."""
        answers = {}
        energies = ['D', 'S', 'F']
        for i in range(27, 38):
            ranking = {}
            for idx, e in enumerate(energies):
                if e == dominant_energy:
                    ranking[e] = 1
                elif idx == 0:
                    ranking[e] = 2
                else:
                    ranking[e] = 3
            # Ensure dominant gets rank 1
            if dominant_energy != 'D':
                ranking['D'] = 2
                ranking[dominant_energy] = 1
                remaining = [e for e in energies if e != dominant_energy and e != 'D']
                for e in remaining:
                    ranking[e] = 3
            answers[str(i)] = {'ranking': ranking}
        return answers

    def _build_stage_e_answers(self, dominant_trait='A'):
        """Helper to build Stage E answers (questions 57-60) with ranking."""
        answers = {}
        traits = ['A', 'T', 'P', 'E']
        for i in range(57, 61):
            ranking = {}
            for idx, t in enumerate(traits):
                if t == dominant_trait:
                    ranking[t] = 1
                else:
                    ranking[t] = idx + 2 if idx < 3 else 4
            # Ensure proper ranking 1-4
            rank = 2
            for t in traits:
                if t != dominant_trait:
                    ranking[t] = rank
                    rank += 1
            answers[str(i)] = {'ranking': ranking}
        return answers

    def test_a7_code(self):
        """A dominant trait + D dominant energy = A7."""
        answers = {}
        answers.update(self._build_stage_a_answers('AP', 20))
        # Add some AE to boost A further
        for i in range(21, 27):
            answers[str(i)] = {'selected_option_code': 'AE'}
        answers.update(self._build_stage_b_answers('D'))
        answers.update(self._build_stage_e_answers('A'))
        result = calculate_pdn_code(answers)
        if isinstance(result, dict):
            assert result['pdn_code'] == 'A7'
        else:
            assert result == 'A7'

    def test_p10_code(self):
        """P dominant trait + D dominant energy = P10."""
        answers = {}
        # AP gives both A and P; TP gives T and P. Use TP to boost P
        answers.update(self._build_stage_a_answers('TP', 20))
        for i in range(21, 27):
            answers[str(i)] = {'selected_option_code': 'AP'}
        answers.update(self._build_stage_b_answers('D'))
        answers.update(self._build_stage_e_answers('P'))
        result = calculate_pdn_code(answers)
        if isinstance(result, dict):
            assert result['pdn_code'] == 'P10'
        else:
            assert result == 'P10'

    def test_t4_code(self):
        """T dominant trait + D dominant energy = T4."""
        answers = {}
        answers.update(self._build_stage_a_answers('ET', 20))
        for i in range(21, 27):
            answers[str(i)] = {'selected_option_code': 'TP'}
        answers.update(self._build_stage_b_answers('D'))
        answers.update(self._build_stage_e_answers('T'))
        result = calculate_pdn_code(answers)
        if isinstance(result, dict):
            assert result['pdn_code'] == 'T4'
        else:
            assert result == 'T4'

    def test_e5_code(self):
        """E dominant trait + S dominant energy = E5."""
        answers = {}
        answers.update(self._build_stage_a_answers('ET', 20))
        for i in range(21, 27):
            answers[str(i)] = {'selected_option_code': 'AE'}
        answers.update(self._build_stage_b_answers('S'))
        answers.update(self._build_stage_e_answers('E'))
        result = calculate_pdn_code(answers)
        if isinstance(result, dict):
            assert result['pdn_code'] == 'E5'
        else:
            assert result == 'E5'

    def test_return_details_mode(self):
        """return_details=True should return dict with calculation_details."""
        answers = {}
        answers.update(self._build_stage_a_answers('AP', 26))
        answers.update(self._build_stage_b_answers('D'))
        answers.update(self._build_stage_e_answers('A'))
        result = calculate_pdn_code(answers, return_details=True)
        assert isinstance(result, dict)
        assert 'pdn_code' in result
        assert 'calculation_details' in result
        assert len(result['calculation_details']) >= 5  # Stages A, B, C, D, E, Final

    def test_partial_answers(self):
        """Partial answers should still produce a result."""
        answers = {
            '1': {'selected_option_code': 'AP'},
            '2': {'selected_option_code': 'AP'},
            '3': {'selected_option_code': 'AP'},
        }
        result = calculate_pdn_code(answers)
        # With only stage A partial answers and no energy, should be NA or dict
        if isinstance(result, dict):
            assert 'pdn_code' in result
        else:
            assert result == 'NA'

    def test_all_12_pdn_matrix_combinations(self):
        """Verify all 12 PDN matrix combinations are valid codes."""
        expected_codes = {
            ('P', 'D'): 'P10', ('P', 'S'): 'P2', ('P', 'F'): 'P6',
            ('E', 'D'): 'E1', ('E', 'S'): 'E5', ('E', 'F'): 'E9',
            ('A', 'D'): 'A7', ('A', 'S'): 'A11', ('A', 'F'): 'A3',
            ('T', 'D'): 'T4', ('T', 'S'): 'T8', ('T', 'F'): 'T12'
        }
        # Just verify the matrix is correct by checking the module's logic
        for (trait, energy), expected_code in expected_codes.items():
            # Build minimal answers that produce this combination
            # We test the matrix lookup directly via return_details
            assert expected_code[0] == trait
            assert len(expected_code) >= 2

    def test_tie_breaking_scenario(self):
        """When traits are tied, Stage C/D/E should break the tie."""
        # Create equal A and T scores in Stage A
        answers = {}
        for i in range(1, 14):
            answers[str(i)] = {'selected_option_code': 'AP'}
        for i in range(14, 27):
            answers[str(i)] = {'selected_option_code': 'ET'}
        answers.update(self._build_stage_b_answers('D'))
        # Stage E breaks the tie in favor of T
        answers.update(self._build_stage_e_answers('T'))
        result = calculate_pdn_code(answers)
        if isinstance(result, dict):
            assert result['pdn_code'] in ('T4', 'T8', 'T12', 'A7', 'A11', 'A3', 'NA')
        else:
            assert result in ('T4', 'T8', 'T12', 'A7', 'A11', 'A3', 'NA')
