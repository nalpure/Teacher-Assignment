from z3 import *

import compute_pulp


def compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[1,1,1,1], worst_case_distance=0, cost_threshold=0, step_size=0.5):
    """
    Find the optimum solution with weights a1, a2, a3, a4
    (average workday deviation, maximum workday deviation, cummulative linear distance, sum of priority 2 assignments)
    Higher weight = More optimized (value minimized)

    Returns all assignment-tuples which occur in the calculated optimal model.
    """

    # double all values as half days can exist - float so Z3 doesn't get confused witht the objective function
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


    # constraint1: number of teachers needed per event
    num_available_per_event = {event : len(list(filter(lambda assignment: assignment[1] == event, possible_assignments))) for event in events}
    for event in events:
        num_teachers_to_assign = min(event_size[event], num_available_per_event[event])
        opt.add(Sum( [If(x[assignment], 1, 0) for assignment in possible_assignments if assignment[1] == event] ) == num_teachers_to_assign)


    for teacher in teachers:
        
        # constraint2: max and min number of events for each teacher
        max_events = len(events)
        min_events = 0
        num_assigned_events = Sum( [If(x[assignment], 1, 0) for assignment in possible_assignments if assignment[0] == teacher] )
        opt.add(num_assigned_events >= min_events, num_assigned_events <= max_events)

    
        # constraint3: teacher can't work in multiple overlapping events
        for overlapping_events in event_overlap_sets:
            opt.add(Sum( [If(x[assignment], 1, 0) for assignment in possible_assignments if assignment[1] in overlapping_events and assignment[0] == teacher] ) <= 1)

        
        # constraint4: delta (absolute over and underload of teacher)
        num_teacher_workdays = Sum( [If(x[assignment], event_durations[assignment[1]], 0) for assignment in possible_assignments if assignment[0] == teacher])
        opt.add(delta_plus[teacher] >= 0, delta_minus[teacher] >= 0)
        opt.add(delta_plus[teacher] - delta_minus[teacher] == num_teacher_workdays - desired_workdays[teacher])


        # constraint5: DELTA (maximum relative deviation of wished to assigned workdays)
        opt.add(DELTA >= (delta_plus[teacher] + delta_minus[teacher]) / desired_workdays[teacher])


    """average_rel_workday_deviation = Sum( [(delta_plus[teacher] + delta_minus[teacher]) / max(1,desired_workdays[teacher]) for teacher in teachers] ) / len(teachers)
    overall_distance = Sum( [If(x[assignment], assignment[3], 0) for assignment in possible_assignments])
    num_prio2 = Sum( [If(x[assignment], float(assignment[2]-1), 0) for assignment in possible_assignments])"""
    average_rel_workday_deviation = Real('average_rel_workday_deviation')
    opt += average_rel_workday_deviation == Sum( [(delta_plus[teacher] + delta_minus[teacher]) / max(1,desired_workdays[teacher]) for teacher in teachers] ) / len(teachers)
    overall_distance = Real('overall_distance')
    opt += overall_distance == Sum( [If(x[assignment], assignment[3], 0) for assignment in possible_assignments])
    num_prio2 = Real('num_prio2')
    opt += num_prio2 == Sum( [If(x[assignment], float(assignment[2]-1), 0) for assignment in possible_assignments])

    opt.add(cost == a1 * average_rel_workday_deviation \
        + a2 * DELTA     \
        + a3 * overall_distance / max(1, worst_case_distance) \
        + a4 * num_prio2 / max(1, sum(event_size))
    )

    def realToFloat(z3_real):
        try:
            return float(str(z3_real.as_decimal(20)).replace('?',''))
        except:
            return z3_real

   
    if(cost_threshold):
        # get near-optimal model with binary search
        print("Searching for near-optimal model...")
        lower_boundary = 0 #- sum([a[3] for a in possible_assignments])
        best_model = None
        
        if opt.check() == sat:
            best_model = opt.model()
            upper_boundary = realToFloat(best_model.evaluate(cost))
        else:
            upper_boundary = lower_boundary

        step=0
        while(upper_boundary > lower_boundary + cost_threshold):
            test_value = max(upper_boundary - (upper_boundary - lower_boundary) * step_size, lower_boundary + cost_threshold)
            #test_value = (upper_boundary + lower_boundary) / 2
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
        print("Best model found!")
        print(realToFloat(best_model.evaluate(average_rel_workday_deviation))*a1)
        print(realToFloat(best_model.evaluate(DELTA))*a2)
        print(realToFloat(best_model.evaluate(overall_distance)) * a3  / worst_case_distance)
        print(realToFloat(best_model.evaluate(num_prio2)) * a4 / sum(event_size))
        print("Overall costs:", realToFloat(best_model.evaluate(cost)), '\n')
        for assignment in possible_assignments:
            if best_model.evaluate(x[assignment]):
                optimal_assignments.append(assignment)

        """for teacher in teachers:
            print(f"{teacher}: d+ {best_model.evaluate(delta_plus[teacher])}, d- {best_model.evaluate(delta_minus[teacher])}")
        print("DELTA:::", best_model.evaluate(DELTA))      
        print("min value:", best_model.evaluate(cost).as_decimal(2))"""
    else:
        print("No model was found!")

    return best_model is not None, optimal_assignments