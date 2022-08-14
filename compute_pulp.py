#-------------------------------------------------------------------------------
# Name:        Benes Assignment Program
# Purpose:     Dieses Tool erstellt Vorschläge für die Einteilung von Teachers für verschiedene Kurse.
#
# Author:      Benedikt Schenk
# Copyright:   © 2022 Benedikt Schenk
#-------------------------------------------------------------------------------


import sys
import pulp
from pulp.constants import *

time_limit = 600
gap_tolerance = 0.01

def compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[1,1,1,1], worst_case_distance=0):
    """
    Find the optimum solution with weights a1, a2, a3, a4
    (average relative workday deviation, maximum relative workday deviation, cummulative linear distance, sum of priority 2 assignments)
    Higher weight = More optimized (value minimized)

    Assigment tuples must be given in the following format: (teacher, event, priority, distance)

    Returns all assignment-tuples which occur in the calculated optimal model.
    """

    if not len(weights) == 4:
        print('Wrong number of weights. Exactly 4 are needed.')
        sys.exit()

    # double all values, as half days can exist
    desired_workdays = {k : int(v*2) for (k,v) in desired_workdays.items()}
    event_durations = {k : int(v*2) for (k,v) in event_durations.items()}
   
    # if no worst case distance is given, compute it (needed for normalization)
    if(worst_case_distance == 0):
        print("Computing worst case distance...")
        worst_case_distance = int(sum([assignment[3] for assignment in compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[0,0,-1,0], worst_case_distance=1)[1]]))
        print(f"Worst case distance is {worst_case_distance*2} km.")
        print(f"Optimizing according to given weights {weights} now...\n\n")

    a1, a2, a3, a4 = [w / max(list(map(abs, weights))) / len(weights) for w in weights] # balance weights (highest weight = 1 or -1)

    assignment_model = pulp.LpProblem("teacher_Assignment_Model", pulp.LpMinimize)

    # create a binary variable to state that a teachers is assigned to an event
    x = pulp.LpVariable.dicts(
        "assignment", possible_assignments, lowBound=0, upBound=1, cat=pulp.LpBinary
    )

    # Trick: optimize under- and overload as variables to bypass absolute value (nonlinear) objective function.
    # The constraints ensure that these are in fact the under- and overload of each teacher
    delta_plus = pulp.LpVariable.dicts(
        "overload", teachers, lowBound=0, upBound=sum(event_durations), cat=LpInteger
    )
    delta_minus = pulp.LpVariable.dicts(
        "underload", teachers, lowBound=0, upBound=max(desired_workdays.values()), cat=LpInteger
    )
    DELTA = pulp.LpVariable(
        "DELTA", lowBound=0, upBound=sum(event_durations)     #sum(event_durations) , max(len(events), max(desired_workdays.values())
    )


    #constraint0: If priority is 3, teacher MUST be assigned
    for assignment in [a for a in possible_assignments if a[2] == 3]:
        assignment_model += (
            x[assignment] == 1,
            f"Must_use_assignment_{assignment}"
        )

    # constraint1: don't assign more teachers for an event than needed
    for event in events:
        assignment_model += (
            pulp.lpSum(x[assignment] for assignment in possible_assignments if assignment[1] == event) <= event_size[event],
            f"Max_teachers_{event}"
        )
    
    for teacher in teachers:
        # constraint2: teacher can't work in overlapping events
        for overlapping_events in event_overlap_sets:
            assignment_model += (
                pulp.lpSum([x[assignment] for assignment in possible_assignments if assignment[1] in overlapping_events and assignment[0] == teacher]) <= 1,
                f"teacher_{teacher}_in_overlapping_events_{overlapping_events}",
            )

    assignment_model.objective = - pulp.lpSum([x[assignment] for assignment in possible_assignments])
    tmp_solution = assignment_model.solve()
    max_possible_assignments = - pulp.value(assignment_model.objective)
    print(str(pulp.LpStatus[tmp_solution]), "; maximum possible number of assignments is: ", max_possible_assignments)

    #constraint3: there should be as many assignments as possible
    assignment_model += (
        pulp.lpSum([x[assignment] for assignment in possible_assignments]) >= max_possible_assignments
    )

    for teacher in teachers:
        # constraint4: delta (absolute over and underload of teacher)
        num_teacher_workdays = pulp.lpSum([x[assignment] * event_durations[assignment[1]] for assignment in possible_assignments if assignment[0] == teacher])
        assignment_model += ( 
            delta_plus[teacher] - delta_minus[teacher] == num_teacher_workdays - desired_workdays[teacher],
            f"Over_Under_Load_{teacher}",
        )

        #constraint5: DELTA (maximum relative deviation of wished to assigned workdays)
        assignment_model += (
            (delta_plus[teacher] + delta_minus[teacher]) / desired_workdays[teacher] <= DELTA,
            f"DELTA_{teacher}", #TODO: check for correctness of normalization
        )

    # define the objective function
    assignment_model.objective = a1 * pulp.lpSum([ (delta_minus[teacher] + delta_plus[teacher]) / max(1, desired_workdays[teacher]) for teacher in teachers ]) / max(1, len(teachers)) \
                        + a2 * DELTA \
                        + a3 * pulp.lpSum([ x[assignment] * assignment[3] for assignment in possible_assignments ]) / max(1,worst_case_distance) \
                        + a4 * (1 - (pulp.lpSum([ x[assignment] * assignment[2] for assignment in possible_assignments]) / sum(event_size)) / 3)

    solution = assignment_model.solve(pulp.PULP_CBC_CMD(maxSeconds=time_limit, gapAbs=gap_tolerance))    # The actual computation - gets optimal model

    if(pulp.LpStatus[solution] == "Optimal"): return_code = 1
    elif(pulp.LpStatus[solution] == "Not Solved"): return_code = 0
    elif(pulp.LpStatus[solution] == "Infeasible"): return_code = -1
    else: return_code = -2

    print("Return Code: ", return_code)

    if return_code == 0 or return_code == 1:
        for teacher in teachers:
            """print(f"delta_plus {teacher}: {delta_plus[teacher].value()}")
            print(f"delta_minus {teacher}: {delta_minus[teacher].value()}")
        print(f"DELTA: {DELTA.value()}")"""
        optimal_assignments = [assignment for assignment in possible_assignments if x[assignment].value() == 1.0]
    else:
        optimal_assignments = []

    return return_code, optimal_assignments

