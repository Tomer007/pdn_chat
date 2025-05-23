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
    for i in range(1, 31):
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

    result['scores'].update(trait_counts)
    dominant_trait = max(trait_counts, key=trait_counts.get)
    result['trait'] = dominant_trait

    print("Stage A: Primary Trait Calculation for T " + str(trait_counts['T']))
    print("Stage A: Primary Trait Calculation for P " + str(trait_counts['P']))
    print("Stage A: Primary Trait Calculation for E " + str(trait_counts['E']))
    print("Stage A: Primary Trait Calculation for A " + str(trait_counts['A']))

    # Stage B: Energy Type Calculation
    energy_counts = {'D': 0, 'S': 0, 'F': 0}
    for i in range(31, 41):
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

    print("Stage B: Energy Type Calculation for D " + str(energy_counts['D']))
    print("Stage B: Energy Type Calculation for S " + str(energy_counts['S']))
    print("Stage B: Energy Type Calculation for F " + str(energy_counts['F']))

    # Stage C: Validation and Tie-Breaking
    for i in range(52, 58):
        if str(i) in answers:
            ranking = answers[str(i)]['ranking']
            traits = list(ranking.keys())
            trait1, trait2 = traits
            value1, value2 = ranking[trait1], ranking[trait2]

            difference = value1 - value2
            score_adjustment = abs(difference) * 2

            if difference > 0:
                result['scores'][trait1] += score_adjustment
                result['scores'][trait2] -= score_adjustment
            elif difference < 0:
                result['scores'][trait1] -= score_adjustment
                result['scores'][trait2] += score_adjustment

    new_dominant_trait = max(result['scores'], key=result['scores'].get)
    if result['scores'][new_dominant_trait] - result['scores'][result['trait']] >= 12:
        result['trait'] = new_dominant_trait

    print("Stage C: Validation and Tie-Breaking for T " + str(result['scores']['T']))
    print("Stage C: Validation and Tie-Breaking for P " + str(result['scores']['P']))
    print("Stage C: Validation and Tie-Breaking for E " + str(result['scores']['E']))
    print("Stage C: Validation and Tie-Breaking for A " + str(result['scores']['A']))

    # Finalizing the PDN code
    pdn_matrix = {
        ('P', 'D'): 'P10', ('P', 'S'): 'P2', ('P', 'F'): 'P6',
        ('E', 'D'): 'E1', ('E', 'S'): 'E5', ('E', 'F'): 'E9',
        ('A', 'D'): 'A7', ('A', 'S'): 'A11', ('A', 'F'): 'A3',
        ('T', 'D'): 'T4', ('T', 'S'): 'T8', ('T', 'F'): 'T12'
    }

    pdn_code = pdn_matrix.get((result['trait'], result['energy']), 'NA')
    result['pdn_code'] = pdn_code

    print("Finalizing the PDN code " + str(pdn_code))

    return pdn_code
