import logging

# Add at the beginning of the file, after imports
logger = logging.getLogger(__name__)

def calculate_pdn_code(answers: dict) -> dict:
    """
    Calculate the PDN code based on user's answers.
    Args:
        answers (dict): Dictionary containing user's answers with question numbers as keys
    Returns:
        dict: Dictionary containing the calculated PDN code and related information
    """
    # Initialize result dictionary
    result = {
        'pdn_code': 'NA',
        'trait': 'Undetermined',
        'energy': 'Undetermined',
        'scores': {'A': 0, 'T': 0, 'P': 0, 'E': 0, 'D': 0, 'S': 0, 'F': 0},
        'explanation': ''
    }

    # Stage A: Primary Trait Calculation
    trait_counts = {'A': 0, 'T': 0, 'P': 0, 'E': 0}
    # answer = data.questions
    for i in range(1, 27):
        if str(i) in answers:
            answer = answers[str(i)]['code']
            if answer == 'AP':
                trait_counts['A'] += 1
                trait_counts['P'] += 1
            elif answer == 'ET':
                trait_counts['E'] += 1
                trait_counts['T'] += 1
            elif answer == 'AE':
                trait_counts['A'] += 1
                trait_counts['E'] += 1
            elif answer == 'TP':
                trait_counts['T'] += 1
                trait_counts['P'] += 1

    for trait, score in trait_counts.items():
        result['scores'][trait] += score
    dominant_trait = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage A: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage A: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage A: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage A: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage A dominant trait %s", dominant_trait)



    # Stage B: Energy Type Calculation
    energy_counts = {'D': 0, 'S': 0, 'F': 0}
    for i in range(27, 38):
        if str(i) in answers:
            ranking = answers[str(i)]['ranking']
            for energy, rank in ranking.items():
                if rank == 1:
                    energy_counts[energy] += 3
                elif rank == 2:
                    energy_counts[energy] += 2
                elif rank == 3:
                    energy_counts[energy] += 1

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
            ranking = answers[str(i)]['ranking']
            traits = list(ranking.keys())
            trait1, trait2 = traits
            value1, value2 = ranking[trait1], ranking[trait2]

            difference = value1 - value2
            score_adjustment = abs(difference)

            if difference > 0:
                result['scores'][trait1] += score_adjustment
                result['scores'][trait2] -= score_adjustment
            elif difference < 0:
                result['scores'][trait1] -= score_adjustment
                result['scores'][trait2] += score_adjustment

    for trait, score in trait_counts.items():
        result['scores'][trait] += score
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
            ranking = answers[str(i)]['ranking']
            # Get the trait combinations and their rankings
            trait_combinations = list(ranking.keys())
            if len(trait_combinations) == 2:
                combo1, combo2 = trait_combinations
                value1, value2 = ranking[combo1], ranking[combo2]

                difference = value1 - value2
                score_adjustment = abs(difference) * 2

                if difference > 0:
                    # Add points to both traits in the winning combination
                    result['scores'][combo1[0]] += score_adjustment
                    result['scores'][combo1[1]] += score_adjustment
                    # Subtract points from both traits in the losing combination
                    result['scores'][combo2[0]] -= score_adjustment/2
                    result['scores'][combo2[1]] -= score_adjustment/2
                elif difference < 0:
                    # Add points to both traits in the winning combination
                    result['scores'][combo2[0]] += score_adjustment
                    result['scores'][combo2[1]] += score_adjustment
                    # Subtract points from both traits in the losing combination
                    result['scores'][combo1[0]] -= score_adjustment/2
                    result['scores'][combo1[1]] -= score_adjustment/2

    # Recalculate dominant trait after all adjustments
    dominant_trait = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage D: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage D: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage D: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage D: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage D dominant trait %s", dominant_trait)

    # StageE: Strengthen Dominant Trait
    trait_counts = {'A': 0, 'T': 0, 'P': 0, 'E': 0}
    for i in range(57, 60):
        if str(i) in answers:
            ranking = answers[str(i)]['ranking']
            for trait, rank in ranking.items():
                if rank == 1:
                    result['scores'][trait] += 8  
                elif rank == 2:
                    result['scores'][trait] += 6
                elif rank == 3:
                    result['scores'][trait] += 4
                elif rank == 4:
                    result['scores'][trait] += 2

    dominant_trait = max(result['scores'], key=result['scores'].get)
    result['trait'] = dominant_trait

    logger.info("Stage E: Trait Calculation for A %s", result['scores']['A'])
    logger.info("Stage E: Trait Calculation for T %s", result['scores']['T'])
    logger.info("Stage E: Trait Calculation for P %s", result['scores']['P'])
    logger.info("Stage E: Trait Calculation for E %s", result['scores']['E'])
    logger.info("Stage E dominant trait %s", dominant_trait)


    # Finalizing the PDN code
    pdn_matrix = {
        ('P', 'D'): 'P10', ('P', 'S'): 'P2', ('P', 'F'): 'P6',
        ('E', 'D'): 'E1', ('E', 'S'): 'E5', ('E', 'F'): 'E9',
        ('A', 'D'): 'A7', ('A', 'S'): 'A11', ('A', 'F'): 'A3',
        ('T', 'D'): 'T4', ('T', 'S'): 'T8', ('T', 'F'): 'T12'
    }

    pdn_code = pdn_matrix.get((result['trait'], result['energy']), 'NA')
    result['pdn_code'] = pdn_code

    logger.info("Finalizing the PDN code %s", pdn_code)

    return pdn_code
