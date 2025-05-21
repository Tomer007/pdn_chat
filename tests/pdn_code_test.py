# Improved PDN Calculation Script
import json

# Load data from the uploaded file
with open('saved_results/temp_answers/E5.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Placeholder for calculated PDN data
result = {
    'pdn_code': 'NA',
    'trait': 'Undetermined',
    'energy': 'Undetermined',
    'scores': {'A': 0, 'T': 0, 'P': 0, 'E': 0, 'D': 0, 'S': 0, 'F': 0},
    'explanation': ''
}

# Stage A: Primary Trait Calculation
trait_counts = {'A': 0, 'T': 0, 'P': 0, 'E': 0}
for i in range(1, 39):
    if str(i) in data:
        answer = data[str(i)]['code']
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

print("Stage A: Primary Trait Calculation for T " + str(trait_counts['T']))
print("Stage A: Primary Trait Calculation for P " + str(trait_counts['P']))
print("Stage A: Primary Trait Calculation for E " + str(trait_counts['E']))
print("Stage A: Primary Trait Calculation for A " + str(trait_counts['A']))

result['scores'].update(trait_counts)
dominant_trait = max(trait_counts, key=trait_counts.get)
result['trait'] = dominant_trait


print("    ---- Stage A: Primary Trait Dominant Is: " + str(result['trait']))
# Stage B: Energy Type Calculation
energy_counts = {'D': 0, 'S': 0, 'F': 0}
for i in range(39, 53):
    if str(i) in data:
        ranking = data[str(i)]['ranking']
        for energy, rank in ranking.items():
            if rank == 1:
                energy_counts[energy] += 3
            elif rank == 2:
                energy_counts[energy] += 2
            elif rank == 3:
                energy_counts[energy] += 1

print("Stage B: Energy Type Calculation for D " + str(energy_counts['D']))
print("Stage B: Energy Type Calculation for S " + str(energy_counts['S']))
print("Stage B: Energy Type Calculation for F " + str(energy_counts['F']))

result['scores'].update(energy_counts)
dominant_energy = max(energy_counts, key=energy_counts.get)
result['energy'] = dominant_energy
print("    ---- Stage B: Energy Dominant is: " + str(result['energy']))

# Stage C: Validation and Tie-Breaking
for i in range(52, 62):
    if str(i) in data:
        ranking = data[str(i)]['ranking']
        # Get the two traits being compared
        traits = list(ranking.keys())
        trait1, trait2 = traits
        value1, value2 = ranking[trait1], ranking[trait2]
        
        # Calculate the difference between the rankings
        difference = value1 - value2
        score_adjustment = abs(difference) * 2 
        
        # Adjust scores based on which trait was ranked higher
        if difference > 0:
            result['scores'][trait1] += score_adjustment
            result['scores'][trait2] -= score_adjustment
        elif difference < 0:
            result['scores'][trait1] -= score_adjustment
            result['scores'][trait2] += score_adjustment

print("Stage C: Validation and Tie-Breaking for T " + str(result['scores']['T']))
print("Stage C: Validation and Tie-Breaking for P " + str(result['scores']['P']))
print("Stage C: Validation and Tie-Breaking for E " + str(result['scores']['E']))
print("Stage C: Validation and Tie-Breaking for A " + str(result['scores']['A']))

new_dominant_trait = max(result['scores'], key=result['scores'].get)
if result['scores'][new_dominant_trait] - result['scores'][result['trait']] >= 12:
    print("Stage C: Dominant Trait score is  " + str(result['scores'][new_dominant_trait] - result['scores'][result['trait']]))
    result['trait'] = new_dominant_trait 
    print("Stage C: New Dominant Trait " + str(new_dominant_trait))
else:
    print("    ---- Stage C: Same Dominant Trait After Validation " + str(new_dominant_trait))

# Stage D: Validation and Tie-Breaking
for i in range(62, 78):
    if str(i) in data:
        ranking = data[str(i)]['ranking']
        traits = list(ranking.keys())
        
        # Process each trait pair
        for trait_pair in traits:
            # Split the trait pair into individual traits
            trait1, trait2 = trait_pair[0], trait_pair[1]
            
            # Get the ranking value for this pair
            value = ranking[trait_pair]
            
            # Calculate score adjustment based on ranking
            score_adjustment = abs(4 - value) * 2 
            
            # Update scores for both traits in the pair
            result['scores'][trait1] += score_adjustment
            result['scores'][trait2] += score_adjustment

print("Stage D: Final scores after validation")
print("T: " + str(result['scores']['T']))
print("P: " + str(result['scores']['P']))
print("E: " + str(result['scores']['E']))
print("A: " + str(result['scores']['A']))

# Check if we need to update the dominant trait
new_dominant_trait = max(result['scores'], key=result['scores'].get)
if result['scores'][new_dominant_trait] - result['scores'][result['trait']] >= 12:
    print("Stage D: Dominant Trait changed to " + str(new_dominant_trait))
    result['trait'] = new_dominant_trait
else:
    print("Stage D: Dominant Trait remains " + str(result['trait']))

# Finalizing the PDN code
pdn_matrix = {
    ('P', 'D'): 'P10', ('P', 'S'): 'P2', ('P', 'F'): 'P6',
    ('E', 'D'): 'E1', ('E', 'S'): 'E5', ('E', 'F'): 'E9',
    ('A', 'D'): 'A7', ('A', 'S'): 'A11', ('A', 'F'): 'A3',
    ('T', 'D'): 'T4', ('T', 'S'): 'T8', ('T', 'F'): 'T12'
}
pdn_code = pdn_matrix.get((result['trait'], result['energy']), 'NA')
result['pdn_code'] = pdn_code

# Explanation in Hebrew
result['explanation'] = (
    f'התשובות לשאלות המפתח הראו דומיננטיות ב-{result["trait"]} ו-{result["energy"]}. '
    f'התוצאה המתקבלת היא קוד PDN: {pdn_code}. '
    'שים לב: ייתכן שחלק מהשאלות חסרות ולכן ייתכן סטיית תוצאה.'
)

# Execute the PDN calculation
if __name__ == '__main__':
    print(json.dumps(result, ensure_ascii=False, indent=2))
