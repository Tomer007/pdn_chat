"""
PDN Calculator Module

This module provides functionality to calculate PDN (Personality Development Number) codes
based on user questionnaire answers. The calculation follows a multi-stage process:

- Stage A: Primary trait calculation (A, T, P, E)
- Stage B: Energy type calculation (D, S, F) 
- Stage C: Validation and tie-breaking for traits
- Stage D: Validation and tie-breaking for energy types
- Stage E: Strengthen dominant trait

The final PDN code is determined by combining the dominant trait and energy type
using a predefined matrix.
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def calculate_pdn_code(answers: Dict[str, Any]) -> str:
    """
    Calculate the PDN code based on user's answers.
    
    Args:
        answers (dict): Dictionary containing user's answers with question numbers as keys
        
    Returns:
        str: The calculated PDN code (e.g., 'A7', 'P10', 'T4', etc.)
    """
    # Initialize result dictionary with proper typing
    result: Dict[str, Any] = {
        'pdn_code': 'NA',
        'trait': 'Undetermined',
        'energy': 'Undetermined',
        'scores': {'A': 0, 'T': 0, 'P': 0, 'E': 0, 'D': 0, 'S': 0, 'F': 0}
    }

    # Stage A: Primary Trait Calculation
    for i in range(1, 27):
        if str(i) in answers:
            answer_data = answers[str(i)]
            # Check if selected_option_code exists and is valid
            if 'selected_option_code' in answer_data and isinstance(answer_data['selected_option_code'], str):
                answer = answer_data['selected_option_code']
                if answer == 'AP':
                    result['scores']['A'] += 1
                    result['scores']['P'] += 1
                elif answer == 'ET':
                    result['scores']['E'] += 1
                    result['scores']['T'] += 1
                elif answer == 'AE':
                    result['scores']['A'] += 1
                    result['scores']['E'] += 1
                elif answer == 'TP':
                    result['scores']['T'] += 1
                    result['scores']['P'] += 1
            else:
                logger.warning("Missing or invalid selected_option_code for question %s", i)
    dominant_trait: str = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage A: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage A: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage A: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage A: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage A dominant trait %s", dominant_trait)

    # Stage B: Energy Type Calculation
    energy_counts: Dict[str, int] = {'D': 0, 'S': 0, 'F': 0}
    for i in range(27, 38):
        if str(i) in answers:
            answer_data = answers[str(i)]
            # Check if ranking data exists and is valid
            if 'ranking' in answer_data and isinstance(answer_data['ranking'], dict):
                ranking = answer_data['ranking']
                for energy, rank in ranking.items():
                    if isinstance(rank, (int, float)) and energy in energy_counts:
                        if rank == 1:
                            energy_counts[energy] += 3
                        elif rank == 2:
                            energy_counts[energy] += 2
                        elif rank == 3:
                            energy_counts[energy] += 1
            else:
                logger.warning("Missing or invalid ranking data for question %s", i)

    result['scores'].update(energy_counts)
    dominant_energy = max(energy_counts, key=energy_counts.get)
    result['energy'] = dominant_energy

    logger.info("Stage B: Energy Type Calculation for D %s", energy_counts['D'])
    logger.info("Stage B: Energy Type Calculation for S %s", energy_counts['S'])
    logger.info("Stage B: Energy Type Calculation for F %s", energy_counts['F'])
    logger.info("Stage B dominant energy %s", dominant_energy)

    # Stage C: Validation and Tie-Breaking
    for i in range(38, 43):
        if str(i) in answers:
            answer_data = answers[str(i)]
            # Check if ranking data exists and is valid
            if 'ranking' in answer_data and isinstance(answer_data['ranking'], dict):
                ranking = answer_data['ranking']
                traits = list(ranking.keys())
                if len(traits) >= 2:
                    trait1, trait2 = traits[0], traits[1]
                    value1, value2 = ranking[trait1], ranking[trait2]

                    if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                        difference = value1 - value2
                        score_adjustment = abs(difference)

                        if difference > 0:
                            result['scores'][trait1] += 1
                            # result['scores'][trait2] -= 1
                        elif difference < 0:
                            # result['scores'][trait1] -= 1
                            result['scores'][trait2] += 1
            else:
                logger.warning("Missing or invalid ranking data for question %s", i)

    dominant_trait = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage C: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage C: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage C: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage C: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage C dominant trait %s", dominant_trait)

    # Stage D: Validation and Tie-Breaking
    for i in range(43, 57):
        if str(i) in answers:
            answer_data = answers[str(i)]
            # Check if ranking data exists and is valid
            if 'ranking' in answer_data and isinstance(answer_data['ranking'], dict):
                ranking = answer_data['ranking']
                # Get the trait combinations and their rankings
                trait_combinations = list(ranking.keys())
                if len(trait_combinations) == 2:
                    combo1, combo2 = trait_combinations
                    value1, value2 = ranking[combo1], ranking[combo2]

                    if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                        difference = value1 - value2
                        score_adjustment = abs(difference) * 2

                        if difference > 0:
                            # Add points to both traits in the winning combination
                            if len(combo1) >= 2:
                                result['scores'][combo1[0]] += 1
                                result['scores'][combo1[1]] += 1
                            # Subtract points from both traits in the losing combination
                            # result['scores'][combo2[0]] -= 1
                            # result['scores'][combo2[1]] -= 1
                        elif difference < 0:
                            # Add points to both traits in the winning combination
                            if len(combo2) >= 2:
                                result['scores'][combo2[0]] += 1
                                result['scores'][combo2[1]] += 1
                            # Subtract points from both traits in the losing combination
                            # result['scores'][combo1[0]] -= 1
                            # result['scores'][combo1[1]] -= 1
            else:
                logger.warning("Missing or invalid ranking data for question %s", i)

    # Recalculate dominant trait after all adjustments
    dominant_trait = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage D: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage D: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage D: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage D: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage D dominant trait %s", dominant_trait)

    # Stage E: Strengthen Dominant Trait
    for i in range(57, 61):
        if str(i) in answers:
            answer_data = answers[str(i)]
            # Check if ranking data exists and is valid
            if 'ranking' in answer_data and isinstance(answer_data['ranking'], dict):
                ranking = answer_data['ranking']
                for trait, rank in ranking.items():
                    if isinstance(rank, (int, float)) and trait in result['scores']:
                        if rank == 1:
                            result['scores'][trait] += 8
                        elif rank == 2:
                            result['scores'][trait] += 4
                        elif rank == 3:
                            result['scores'][trait] += 2
                        elif rank == 4:
                            result['scores'][trait] += 0
            else:
                logger.warning("Missing or invalid ranking data for question %s", i)

    dominant_trait = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage E: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage E: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage E: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage E: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage E dominant trait %s", dominant_trait)

    # Finalizing the PDN code
    pdn_matrix: Dict[Tuple[str, str], str] = {
        ('P', 'D'): 'P10', ('P', 'S'): 'P2', ('P', 'F'): 'P6',
        ('E', 'D'): 'E1', ('E', 'S'): 'E5', ('E', 'F'): 'E9',
        ('A', 'D'): 'A7', ('A', 'S'): 'A11', ('A', 'F'): 'A3',
        ('T', 'D'): 'T4', ('T', 'S'): 'T8', ('T', 'F'): 'T12'
    }

    pdn_code: str = pdn_matrix.get((result['trait'], result['energy']), 'NA')
    result['pdn_code'] = pdn_code

    logger.info("Finalizing the PDN code %s", pdn_code)

    return pdn_code
