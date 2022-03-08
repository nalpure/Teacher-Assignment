import sys
import pulp
from pulp.constants import LpInteger


def compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[1,1,1,1], worst_case_distance=0):
    """
    Find the optimum solution with weights a1, a2, a3, a4
    (average relative workday deviation, maximum relative workday deviation, cummulative linear distance, sum of priority 2 assignments)
    Higher weight = More optimized (value minimized)

    Returns all assignment-tuples which occur in the calculated optimal model.
    """

    # double all values, as half days can exist
    desired_workdays = {k : int(v*2) for (k,v) in desired_workdays.items()}
    event_durations = {k : int(v*2) for (k,v) in event_durations.items()}
   
    # if no worst case distance is given, compute it (needed for normalization)
    if(worst_case_distance == 0):
        print("Computing worst case distance...")
        worst_case_distance = sum([assignment[3] for assignment in compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[0,0,-1,0], worst_case_distance=1)[1]])
        print(f"Worst case distance is {worst_case_distance*2}km.")
        print("Optimizing according to given weights now...\n\n")

    if not len(weights) == 4:
        print('Wrong number of weights. Exactly 4 are needed.')
        sys.exit()
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

    # define the objective function
    assignment_model.objective = a1 * pulp.lpSum([ (delta_minus[teacher] + delta_plus[teacher]) / max(1, desired_workdays[teacher]) for teacher in teachers ]) / max(1, len(teachers)) \
                        + a2 * DELTA \
                        + a3 * pulp.lpSum([ x[assignment] * assignment[3] / max(1,worst_case_distance) for assignment in possible_assignments ]) \
                        + a4 * pulp.lpSum([ x[assignment] * (assignment[2] - 1) for assignment in possible_assignments ]) / max(1, sum(event_size))



    # constraint1: number of teachers needed per event
    # TODO: change it not to a restriction, but to an optimization variable?
    num_available_per_event = {event : len(list(filter(lambda assignment: assignment[1] == event, possible_assignments))) for event in events}
    for event in events:
        num_teachers_to_assign = min(event_size[event], num_available_per_event[event])
        assignment_model += (
            pulp.lpSum([x[assignment] for assignment in possible_assignments if assignment[1] == event]) == num_teachers_to_assign,
            f"Must_be_teacherd_{event}",
        )
    
    for teacher in teachers:

        # constraint2: max and min number of events for each teacher
        max_events = len(events)
        min_events = 0
        assignment_model += (
            pulp.lpSum([x[assignment] for assignment in possible_assignments if assignment[0] == teacher]) >= min_events,
            f"Must_teacher_minimal_{teacher}",
        )
        assignment_model += (
            pulp.lpSum([x[assignment] for assignment in possible_assignments if assignment[0] == teacher]) <= max_events,
            f"Must_teacher_maximum_{teacher}",
        )

        # constraint3: teacher can't work in multiple overlapping events
        for overlapping_events in event_overlap_sets:
            assignment_model += (
                pulp.lpSum([x[assignment] for assignment in possible_assignments if assignment[1] in overlapping_events and assignment[0] == teacher]) <= 1,
                f"teacher_{teacher}_in_overlapping_events_{overlapping_events}",
            )

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

    status = assignment_model.solve()    # The actual computation - gets optimal model

    optimal_found = pulp.LpStatus[status] == 'Optimal'

    if optimal_found:
        for teacher in teachers:
            """print(f"delta_plus {teacher}: {delta_plus[teacher].value()}")
            print(f"delta_minus {teacher}: {delta_minus[teacher].value()}")
        print(f"DELTA: {DELTA.value()}")"""
        optimal_assignments = [assignment for assignment in possible_assignments if x[assignment].value() == 1.0]
    else:
        optimal_assignments = []

    return optimal_found, optimal_assignments

