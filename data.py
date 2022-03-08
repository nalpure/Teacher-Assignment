#-------------------------------------------------------------------------------
# Name:        teacher-Einteilungstool
# Purpose:     Dieses Tool erstellt Vorschläge für die Einteilung von teachers für verschiedene Kurse.
#
# Author:      Benedikt Schenk
#-------------------------------------------------------------------------------

import sys
from openpyxl import load_workbook
from openpyxl.styles import Font
import geopy.distance
import openpyxl
from openpyxl.styles import Font



#TODO: make names variable
availabilities_sheet_name = "Verfügbarkeiten"
desired_workdays_sheet_name = "Anzahl Wunschtage"
teacher_coordinates_sheet_name = "guides"
event_coordinate_sheet_name = "events"



def get_problem(availability_filepath, coordinates_filepath):

    # import excel sheets
    workbook1 = load_workbook(availability_filepath)
    availabilities_sheet = workbook1[availabilities_sheet_name]
    desired_workdays_sheet = workbook1[desired_workdays_sheet_name]

    workbook2 = load_workbook(coordinates_filepath)
    teacher_coordinates_sheet = workbook2[teacher_coordinates_sheet_name]
    event_coordinates_sheet = workbook2[event_coordinate_sheet_name]

    # dictionary with lat/long coordinates for each teacher
    teacher_coordinates_dict = {row[0][0] : row[0][1] for row in list(zip(teacher_coordinates_sheet.values))[2:]}

    # dictionary with lat/long coordinates for each event
    event_coordinates_dict = {}
    event_coordinate_sheet_as_dict = {row[0][0] : row[0][1] for row in list(zip(event_coordinates_sheet.values))[2:]}
    for row in availabilities_sheet.iter_rows(min_row=3, min_col=1, max_col=2):
        location = row[1].value
        if not location: continue 
        if not location in event_coordinate_sheet_as_dict:
            print("Error: Location \'" + str(location) + "\' could not be found in the Event Location Sheet")
            sys.exit()
        coordinate = event_coordinate_sheet_as_dict[location]
        event_coordinates_dict[row[0].value] = coordinate


    # data initialation
    teachers, events, event_overlap_sets = [],[],[]
    desired_workdays, event_size, event_durations = {},{},{}

    for row in desired_workdays_sheet.iter_rows(min_row=3, min_col=1, max_col=2):
        teacher = row[0].value
        if not teacher: break
        teachers.append(teacher)                         # names of teachers

        if(row[1].value > 0):
            desired_workdays[teacher] = row[1].value * 2      # how many days (times two !!) each teacher wants to work
        else:
            print("Error: Please exclude teachers who don't wish to work.")
            sys.exit()


    for row in availabilities_sheet.iter_rows(min_row=3, min_col=1, max_col=5):
        event = row[0].value
        if not event: continue
        events.append(event)                         # event IDs
        event_durations[event] = row[2].value * 2    # how many days (times two !!) an event lasts
        event_size[event] = row[3].value             # how many teachers are needed per event


        # read overlaps
        overlaps = []
        if type(row[4].value) is str:               
            overlaps = list(map(int, row[4].value.split(";")))
        elif type(row[4].value) is int:
            overlaps = [row[4].value]  
        elif row[4].value is None:
            continue
        else:
            print(f"Error: Could not identify overlapping event \'{row[4].value}\'. Please use \';\' to seperate event ids.")
            sys.exit()

        # find overlapping events and put according event IDs into groups (sets)
        new_group = set()
        for overlap_id in list(filter(lambda x: event < x, overlaps)):
            group_found = False
            for group in event_overlap_sets:
                if overlap_id in group:
                    group.add(event)
                    group_found = True
            if not group_found:
                new_group.add(overlap_id)

        if new_group:
            new_group.add(event)
            event_overlap_sets.append(new_group)

    # an assignment is a list (teacher, event, priority, distance), 
    # eg: ("A", 3, 1, 10) means teacher A is assigned to event 3, which he entered as priority 1 and has 10km of distance to
    possible_assignments = []
    def add_possible_assignments(prio):
        for event, available_teachers in zip(events, availabilities_sheet.iter_rows(min_row=3, min_col=7+prio, max_col=7+prio)):
        
            if not available_teachers[0].value:   # if no teachers available
                continue    
            
            for teacher in available_teachers[0].value.replace(" ", "").split(","):
                if teacher == "":
                    continue

                if not teacher in teachers:
                    print("Error: The teacher-name \'" + teacher + "\' does not seem to match any teacher in the 'desired assignments' sheet")
                    sys.exit()

                coordinate_teacher = tuple(map(float, teacher_coordinates_dict[teacher].split(",")))
                coordinate_event = tuple(map(float, event_coordinates_dict[event].split(",")))
                distance = geopy.distance.distance(coordinate_teacher, coordinate_event).km

                possible_assignments.append((teacher, event, prio, distance))

    add_possible_assignments(1)
    add_possible_assignments(2)

    if(len(teachers) > 20):
        print("Error: Maximale Anzahl an teachers überschritten.")
        sys.exit()
    if(len(events) > 40):
        print("Error: Maximale Anzahl an Events überschritten.")


    """print(f'\teachers={[t[0:3] for t in teachers]}\npossible_assignments={[(t[0:3], e, p, d) for (t,e,p,d) in possible_assignments]}', '\ndesired_workdays=', {t[0:3] : v for (t,v) in desired_workdays.items()})
    print(f"events={events}\nevent_overlap_sets={event_overlap_sets}\nevent_size={event_size}\nevent_durations={event_durations}\nnum_available_per_event={num_available_per_event}")
    """

    return teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments

    


def write_model(output_filename, teachers, events, desired_workdays, event_size, event_durations, assignments):

    final_assignments_dict_event = {}   # event as key, assignments for this event as value    
    final_assignments_dict_teacher = {}   # same but teacher as key

    for assignment in assignments:
        teacher, event = assignment[0], assignment[1]

        if not teacher in final_assignments_dict_teacher:
            final_assignments_dict_teacher[teacher] = []
        
        if not event in final_assignments_dict_event:
            final_assignments_dict_event[event] = []
        
        final_assignments_dict_event[event].append(assignment)
        final_assignments_dict_teacher[teacher].append(assignment)     


    BLACK = '00000000'
    RED = '00FF0000'
    GREEN = '00008000'
    BLUE = '000000FF'

    solution_sheet_name="Solution Sheet"
    statistics_sheet_name = "Statistics Sheet"

    workbook = openpyxl.Workbook()
    del workbook[workbook.active.title]

    workbook.create_sheet(title=solution_sheet_name)
    solution_sheet = workbook[solution_sheet_name]
    workbook.create_sheet(title=statistics_sheet_name)
    statistics_sheet = workbook[statistics_sheet_name]
    
    c1 = solution_sheet["A1"]
    c2 = solution_sheet["C1"]
    c1.value = "Event"
    c2.value = "teachers"
    c1.font = c2.font = Font(bold=True)

    for curr_row, event in enumerate(events): 

        event_cell = solution_sheet.cell(row=curr_row+3, column=1)
        event_cell.value = event

        num_assigned_teachers = 0

        # write assigned teacher names
        if event in final_assignments_dict_event:
            for teacher_num, assignment in enumerate(final_assignments_dict_event[event]):
                num_assigned_teachers += 1
                teacher_cell = solution_sheet.cell(row=curr_row+3, column=teacher_num+3)
                teacher_cell.value = assignment[0]

                # change color according to priority
                if(assignment[2] == 1):
                    teacher_cell.font = Font(color=GREEN)
                else:
                    teacher_cell.font = Font(color=BLUE)
        
        # mark empty spots
        for i in range(num_assigned_teachers, event_size[event]):
            teacher_cell = solution_sheet.cell(row=curr_row+3, column=3+i)
            teacher_cell.value = 'XXX'
            teacher_cell.font = Font(color=RED)



    def get_num_prio2(teacher="None"):
        if teacher == "None":
            sum = 0
            for teacher in teachers:
                sum += get_num_prio2(teacher)
            return sum

        if not teacher in final_assignments_dict_teacher:
            return 0

        sum = 0
        for assignment in final_assignments_dict_teacher[teacher]:
            sum += assignment[2] - 1    # adds 1 if prio is 2
        return sum


    def write(row, column, value, bold=False):
        c = statistics_sheet.cell(row=row, column=column)
        c.value = value
        c.font=Font(bold=bold)
    
    write(1,1,"teacher", True)
    write(1,2,"Arbeitstage", True)
    write(1,3,"Gewünschte Tage", True)
    write(1,4,"Abweichung in %", True)


    first_teacher_row = 3
    abs_deviations = []
    relative_deviations = []
    for i, teacher in enumerate(teachers):
        num_workdays = 0
        if(teacher in final_assignments_dict_teacher):
            for assignment in final_assignments_dict_teacher[teacher]:
                num_workdays += event_durations[assignment[1]]

        deviation = num_workdays - desired_workdays[teacher]
        abs_deviations.append(abs(deviation))

        deviation_percentage = deviation / desired_workdays[teacher]
        relative_deviations.append(abs(deviation_percentage))

        write(first_teacher_row+i,1,teacher)
        write(first_teacher_row+i,2,num_workdays / 2)
        write(first_teacher_row+i,3,desired_workdays[teacher] / 2)
        write(first_teacher_row+i,4,str(round(100 * deviation_percentage)) + "%")


    overall_distance = sum([assignment[3] for assignment in assignments]) * 2
    first_statistics_row = len(teachers) + 4

    write(first_statistics_row, 1, "Durchschnittl Abweichung")
    write(first_statistics_row, 4, str(round(100 * sum(relative_deviations) / len(relative_deviations))) + '%')

    write(first_statistics_row+1, 1, "Maxim. Abweichung")
    write(first_statistics_row+1, 4, str(round(100 * max(relative_deviations))) + "%")

    write(first_statistics_row+2, 1, "Gefahrene km:")
    write(first_statistics_row+2, 4, round(overall_distance))

    write(first_statistics_row+3, 1, "Anteil prio2")
    write(first_statistics_row+3, 4, str(round(100 * get_num_prio2() / sum(event_size))) + '%')

    write(first_statistics_row+4, 1, "Durchschnittl. abs Abweichung")
    write(first_statistics_row+4, 4, round(sum(abs_deviations) / len(abs_deviations) / 2, 1))

    workbook.save(output_filename)

    print(f"Done. Saved as {output_filename}.")


