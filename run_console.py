import compute_pulp
import compute_z3
import data

import time
from os import path



def main():
    
    print("Willkommen zum Kurseinteilung-Tool.")
    print("Daten werden geladen...")
    time.sleep(2)

    teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments = \
        data.get_custom_data("input/Wunschtage-Kopie.xlsx", "input/Koordinaten.xlsx")

    solver_name = ''
    while not (solver_name == 'pulp' or solver_name == 'z3'):
        print("Wählen sie PuLP oder Z3 als Solver (pulp/z3):")
        solver_name = input().lower()


    str = ""
    while not (str == 'ja' or str == 'nein'):
        print("Möchten Sie mit der Standard-Gewichtung fortfahren? (ja / nein)")
        str = input().lower()

    if(str == 'nein'):
        standard_weights = False
    else:
        standard_weights = True

    weight_names = ["Durchschnittliche Abweichung der Arbeitstage", "Maximale Abweichung der Arbeitstage", "Distanz", "Priorität"]

    if standard_weights:
        weights = [1,1,1,1]
    else:
        print("\nWählen Sie 4 Gewichtungen zwischen 0 und 10. Bitte im README.txt nachlesen.\n")
        time.sleep(1)
        weights = []
        for i in range(4):
            valid_input = False
            while(not valid_input):
                print(f"Bitte geben Sie einen Wert für Gewichtung {i+1} an ({weight_names[i]})")
                str = input()
                try:
                    value = float(str)
                except:
                    print("Fehlerhafte Eingabe - Ungültiger Wert.")
                    continue

                if(value >= -10) and (value <= 10):
                    valid_input = True

                weights.append(value)
        

    valid_input = False
    while not valid_input:
        illegal_characters = ['\\',':','*','?','"','<','>','|']
        print("Wählen Sie einen Namen für die Output Datei.")
        output_filename = 'output/' + input()

        character_matches = [char in output_filename for char in illegal_characters]
        split_filename = output_filename.split('.')
        
        if any(character_matches):
            print("Fehlerhafte Eingabe - Der Dateiname darf folgende Zeichen nicht beinhalten:", illegal_characters,"\n")
        elif not len(split_filename) == 2:
            print(f"Error, {output_filename} is not a vaild output filename")
        elif not split_filename[1] == 'xlsx':
            print("Error, please specify a '.xlsx' file as output file")
        else:
            valid_input = True

        file_path, file_extension = split_filename
        
    # add number to output filename if it already exists
    i = 0
    while path.exists(output_filename):
        i += 1
        output_filename = f"{file_path}({i}).{file_extension}"
    

    if(solver_name == 'pulp'):
        optimal_assignments = compute_pulp.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights)
    elif(solver_name == 'z3'):
        print("Wählen Sie einen 'cost-threshold' >= 0. Für das optimale Ergebnis, wählen Sie '0':")
        cost_threshold = -1
        while cost_threshold < 0:
            inp = input()
            try:
                print(inp)
                cost_threshold = float(inp)
            except ValueError:
                print("No valid number.")
        optimal_assignments = compute_z3.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights, cost_threshold=cost_threshold)

    data.write_model(output_filename, teachers, events, desired_workdays, event_size, event_durations, optimal_assignments)


if __name__ == '__main__':
    main()