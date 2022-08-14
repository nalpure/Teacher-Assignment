from z3 import *

def compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[1,1,1,1], worst_case_distance=0, cost_threshold=0, step_size=0.5):
    """
    Find the (sub-)optimum solution with weights a1, a2, a3, a4
    (average relative workday deviation, maximum relative workday deviation, cummulative linear distance, sum of priority 2 assignments)
    Higher weight = More optimized (value minimized)

    Assigment tuples must be given in the following format: (teacher, event, priority, distance)

    If a cost-threshold is given, not the optimum but a near-optimum (how close it is to the optimum is specified by cost-threshold) will 
    be calculated via binary search. The step_size variable specifies the relative step size between each iteration.

    Returns all assignment-tuples which occur in the calculated (sub-)optimal model.
    """

    # double all values as half days can exist - float so Z3 doesn't get confused with the objective function
    desired_workdays = {k : float(v*2) for (k,v) in desired_workdays.items()}
    event_durations = {k : float(v*2) for (k,v) in event_durations.items()}

    # if no worst case distance is given, compute it (needed for normalization)
    if(worst_case_distance == 0):
        print("Computing worst case distance...")
        worst_case_distance = sum([assignment[3] for assignment in compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, [0,0,-1,0],1, cost_threshold, step_size)[1]])
        print(f"Worst case distance is {worst_case_distance*2}km.")
        print("Optimizing according to given weights now...\n\n")

    if not len(weights) == 4:
        print('Wrong number of weights. Exactly 4 are needed.')
        sys.exit()
    a1, a2, a3, a4 = [w / max(list(map(abs, weights))) / len(weights) for w in weights] # balance weights (highest weight = 1/4 or -1/4)

    
    # key: assignment tuple, value: z3-Bool (the decision variable)
    x = {assignment : Bool('e%i_%s' % (assignment[1], assignment[0])) for assignment in possible_assignments}

    delta_plus = {teacher : Real('d+_%s' % teacher) for teacher in teachers}
    delta_minus = {teacher : Real('d-_%s' % teacher) for teacher in teachers}
    DELTA = Real('DELTA')
    cost = Real('cost')

    if cost_threshold:
        opt = Solver()
    else:
        opt = Optimize()

    #constraint0: If priority is 3, teacher MUST be assigned
    for assignment in [a for a in possible_assignments if a[2] == 3]:
        opt.add(
            x[assignment] == 1,
        )

    # constraint1: number of teachers needed per event
    num_available_per_event = {event : len(list(filter(lambda assignment: assignment[1] == event, possible_assignments))) for event in events}
    for event in events:
        num_teachers_to_assign = min(event_size[event], num_available_per_event[event])
        opt.add(Sum( [If(x[a], 1, 0) for a in possible_assignments if a[1] == event] ) == num_teachers_to_assign)


    for teacher in teachers:
        # constraint2: teacher can't work in overlapping events
        for overlapping_events in event_overlap_sets:
            opt.add(Sum( [If(x[assignment], 1, 0) for assignment in possible_assignments if assignment[1] in overlapping_events and assignment[0] == teacher] ) <= 1)

        # constraint3: delta (absolute over and underload of teacher)
        num_teacher_workdays = Sum( [If(x[assignment], event_durations[assignment[1]], 0) for assignment in possible_assignments if assignment[0] == teacher])
        opt.add(delta_plus[teacher] >= 0, delta_minus[teacher] >= 0)
        opt.add(delta_plus[teacher] - delta_minus[teacher] == num_teacher_workdays - desired_workdays[teacher])

        # constraint4: DELTA (maximum relative deviation of wished to assigned workdays)
        opt.add(DELTA >= (delta_plus[teacher] + delta_minus[teacher]) / desired_workdays[teacher])

    average_rel_workday_deviation = Real('average_rel_workday_deviation')
    opt += average_rel_workday_deviation == Sum( [(delta_plus[teacher] + delta_minus[teacher]) / max(1,desired_workdays[teacher]) for teacher in teachers] ) / len(teachers)
    overall_distance = Real('overall_distance')
    opt += overall_distance == Sum( [If(x[assignment], assignment[3], 0) for assignment in possible_assignments])
    sum_priorities = Real('num_prio2')
    opt += sum_priorities == Sum( [If(x[assignment], float(assignment[2]), 0) for assignment in possible_assignments])

    opt.add(cost == a1 * average_rel_workday_deviation \
        + a2 * DELTA     \
        + a3 * overall_distance / max(1, worst_case_distance) \
        + a4 * (1 - ((sum_priorities / sum(event_size)) / 4))
    )

    def realToFloat(z3_real):
        try:
            return float(str(z3_real.as_decimal(20)).replace('?',''))
        except:
            return z3_real

   
    if(cost_threshold):
        # get near-optimal model with binary search
        print("Searching for near-optimal model...")
        lower_boundary = 0
        best_model = None
        
        if opt.check() == sat:
            best_model = opt.model()
            upper_boundary = realToFloat(best_model.evaluate(cost))
        else:
            upper_boundary = lower_boundary

        step=0
        while(upper_boundary > lower_boundary + cost_threshold):
            test_value = max(upper_boundary - (upper_boundary - lower_boundary) * step_size, lower_boundary + cost_threshold)
            opt.push()
            opt.add(cost < test_value)
            print(f"Optimum is between {lower_boundary} and {upper_boundary}, searching for cost < ", test_value)
    
            if opt.check() == sat:
                best_model = opt.model()
                upper_boundary = realToFloat(best_model.evaluate(cost))
                print("sat")
            else:
                lower_boundary = test_value
                print("unsat")
            
            opt.pop()
            step+=1
        print(f"Finished after {step} steps.")
    else:
        # get optimal model with vZ
        print("Computing optimal model...")
        best_model=None
        opt.minimize(cost)
        if opt.check() == sat:
            best_model = opt.model()


    # return optimal assignments
    optimal_assignments = []
    if best_model:
        print("Z3 Best model found!")
        print(realToFloat(best_model.evaluate(average_rel_workday_deviation))*a1)
        print(realToFloat(best_model.evaluate(DELTA))*a2)
        print(realToFloat(best_model.evaluate(overall_distance)) * a3  / worst_case_distance)
        print(realToFloat(best_model.evaluate(sum_priorities)) * a4 / sum(event_size))
        print("Overall costs:", realToFloat(best_model.evaluate(cost)), '\n')
        for assignment in possible_assignments:
            if best_model.evaluate(x[assignment]):
                optimal_assignments.append(assignment)
    else:
        print("No model was found!")

    if best_model is None:
        return_code = -1
    else: 
        return_code = 1

    return return_code, optimal_assignments