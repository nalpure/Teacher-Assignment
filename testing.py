from openpyxl.styles import Font
import openpyxl
import compute_pulp
import compute_z3
import time
import copy
import json
import random


names_file = 'testing/names.json'
input_filename = 'testing/input.xlsx'


# taken from https://stackoverflow.com/questions/4265546/python-round-to-nearest-05
def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int( n/precision+correction ) * precision


def generate_rand_input(num_teachers, num_events, overlap_chance, workdays_mean, workdays_deviation, event_size_mean, event_size_deviation, event_duration_mean, event_duration_deviation, num_availabilities_mean, num_availabilities_deviation, distance_mean, distance_deviation):
    """ 
    Input: Various problem-size / randomization variables
    Output: The describing variables of a randomized problem
    """
    # teachers
    f = open(names_file)
    json_content = json.load(f)
    all_names = set()
    all_names.update(json_content['girls'] + json_content['boys'])
    
    teachers=[]
    for _ in range(num_teachers):
        teachers.append(all_names.pop())
    f.close()
    
    # events
    events = list(range(num_events))

    # overlapping events
    event_overlap_sets = []
    for event in events:
        num_overlaps = 0
        while(random.random() <= overlap_chance):
            num_overlaps += 1

        if num_overlaps > 0:
            event_overlap_sets.append(set(range(event, min(event + num_overlaps + 1, num_events))))

    # desired workdays
    desired_workdays = {}
    for teacher in teachers:
        desired_workdays[teacher] = max(0.5, round_to(random.gauss(mu=workdays_mean, sigma=workdays_deviation), 0.5))

    # event sizes
    event_size={}
    for event in events:
        event_size[event] = max(1, int(random.gauss(mu=event_size_mean, sigma=event_size_deviation)))

    # event durationss
    event_durations={}
    for event in events:
        event_durations[event] = max(1, round_to(random.gauss(mu=event_duration_mean, sigma=event_duration_deviation), 0.5) * 2)

    # possible assignments
    possible_assignments = []
    for teacher in teachers:
        availabilities = min(len(events), max(0, int(random.gauss(mu=num_availabilities_mean, sigma=num_availabilities_deviation))))
        
        available_events = copy.deepcopy(events)
        selected_events = []
        for _ in range(availabilities):
            selected_events.append(available_events.pop(random.randint(0, len(available_events)-1)))

        for e in selected_events:
            dist = max(0, int(random.gauss(mu=distance_mean, sigma=distance_deviation)))
            prio = random.randint(1,2)
            possible_assignments.append((teacher, e, prio, dist))

    return teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments



def write_benchmarks(sheet, test_num, solver_num, time, cost, num_solvers, color='black'):
    color_codes = {'black':'00000000', 'red':'00FF0000', 'green':'00008000', 'blue':'000000FF'}

    # write time
    cell = sheet.cell(row = 6+test_num, column = 22+solver_num)
    cell.value = time
    cell.font = Font(color=color_codes[color])

    # write cost
    cell = sheet.cell(row = 6+test_num, column = 22+solver_num+num_solvers+1)
    cell.value = cost



def get_next_input(time_sheet):
    """
    Returns the data of the first row in input file, which has no execution times yet.
    If an empty row is read, return None's.
    """
    
    # find out the first test case which was not yet executed
    test_num = 0
    num_rows = 0
    for row in time_sheet.iter_rows(min_row=6):
        if row[0].value is None:
            break
        num_rows += 1 
        if row[21].value is None:
            break
        test_num += 1
    
    # return if all tests were executed
    if test_num == num_rows:
        return None, None, None

    # get input data
    rv = []       # randomization variables
    weights = []
    for i, cell in enumerate(time_sheet[test_num+6]):
        if i in [3,9,15,20]:
            continue
        if i <= 14:
            rv.append(int(cell.value))
        elif i <= 19:
            weights.append(float(cell.value))

    return test_num, rv, weights



def get_cost(assignments, worst_distance, weights, teachers, desired_workdays, event_durations, event_size):
            a1, a2, a3, a4 = [w / max(list(map(abs, weights))) / len(weights) for w in weights] # balance weights (highest weight = 1/4 or -1/4)
            num_assigned_workdays = {t : sum([event_durations[a[1]] for a in assignments if a[0] == t]) for t in teachers}
            rel_workday_deviations = {t : abs(num_assigned_workdays[t] - desired_workdays[t]) / desired_workdays[t] for t in teachers}
            average_rel_workday_deviation = sum(rel_workday_deviations.values()) / len(rel_workday_deviations)
            overall_distance = sum([a[3] for a in assignments])
            num_prio2 = len(list(filter(lambda a: a[2] == 2, assignments)))
            DELTA = max(rel_workday_deviations.values())

            print('weights:', a1, a2, a3, a4)
            print(a1 * average_rel_workday_deviation)
            print(a2 * DELTA)
            print(a3 * overall_distance / worst_distance)
            print(a4 * num_prio2 / max(1, sum(event_size)))
            
            cost = a1 * average_rel_workday_deviation\
                    + a2 * DELTA \
                    + a3 * overall_distance / worst_distance \
                    + a4 * num_prio2 / max(1, sum(event_size))
            print('overall:', cost)
            return cost



def main():
    workbook = openpyxl.load_workbook(input_filename)
    time_sheet = workbook.active
    first_row = time_sheet[4]
    solver_names = list(filter(lambda x: x is not None, list(map(lambda x: x.value, first_row[21:-1]))))

    while(True):
        test_num, rv, weights = get_next_input(time_sheet)
        if test_num is None:
            break

            # generate random TA problem
        teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments =\
            generate_rand_input(rv[0], rv[1], rv[2], rv[3], rv[8], rv[4], rv[9], rv[5], rv[10], rv[6], rv[11], rv[7], rv[12])

        print(f"\n\n\n--- TEST #{test_num} ---")
        print('\nsolvers:', solver_names)
        print('\nteachers:', len(teachers))
        print('\nevents:', len(events))
        print('\nevent_overlaps:', event_overlap_sets)
        print('\ndesired_workdays:', desired_workdays)
        print('\nevent sizes:', event_size)
        print('\nevent duration', event_durations)
        print('\npossible assignments', possible_assignments)

        worst_distance = max(1, sum([assignment[3] for assignment in compute_pulp.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[0,0,-1,0], worst_case_distance=1)[1]]))

        # compute solution and track time for each solver
        for i, solver_name in enumerate(solver_names):
            print(f"\n\n\n--- SOLVING TEST #{test_num} WITH SOLVER {solver_name} ---\n")
            start_time = time.time()
            if solver_name == 'pulp':
                optimal_found, assignments = compute_pulp.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights, worst_distance)
            else:
                cost_threshold = float(solver_name.split('-')[1])
                step_size = float(solver_name.split('-')[2])
                optimal_found, assignments = compute_z3.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights, worst_distance,cost_threshold, step_size)
            comp_time = time.time() - start_time
            cost = get_cost(assignments, worst_distance, weights, teachers, desired_workdays, event_durations, event_size)
            write_benchmarks(time_sheet, test_num, i, comp_time, cost, len(solver_names), color = 'black' if optimal_found else 'red')
            workbook.save(input_filename)

    print("Finished.")



if __name__ == '__main__':
    main()