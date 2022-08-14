#-------------------------------------------------------------------------------
# Name:        Benes Assignment Program
# Purpose:     Dieses Tool erstellt Vorschläge für die Einteilung von Teachers für verschiedene Kurse.
#
# Author:      Benedikt Schenk
# Copyright:   © 2022 Benedikt Schenk
#-------------------------------------------------------------------------------


import tkinter as tk

from tkinter import font  as tkfont
from tkinter import filedialog as fd
from tkinter import *

import data
import compute_pulp as pulp
import sys
from contextlib import redirect_stderr, redirect_stdout
import traceback
from datetime import datetime

# parts taken from https://www.semicolonworld.com/question/42826/switch-between-two-frames-in-tkinter
# and from https://github.com/iamcodefoxx/ATM/blob/master/atm.py





class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        frame = PageWeights(parent=container, controller=self)
        self.frames["PageWeights"] = frame
        frame.grid(row=0, column=0, sticky="nsew")

        frame = PageHelp(parent=container, controller=self)
        self.frames["PageHelp"] = frame
        frame.grid(row=0, column=0, sticky="nsew")

        frame = StartPage(parent=container, controller=self, page_weights=self.frames["PageWeights"])
        self.frames["StartPage"] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        

        self.show_frame("StartPage")
        sys.stdout.flush()

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class PageWeights(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text="Selected Weights", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        self.scale1 = Scale(self, label="Weight 1 (Workdays)", from_=0, to=2, length=200, resolution=0.1, orient=HORIZONTAL)
        self.scale1.set(1.0)
        self.scale1.pack()

        self.scale2 = Scale(self, label="Weight 2 (Distance)", from_=0, to=2, length=200, resolution=0.1, orient=HORIZONTAL)
        self.scale2.set(1.0)
        self.scale2.pack()

        self.scale3 = Scale(self, label="Weight 3 (Priorities)", from_=0, to=2, length=200, resolution=0.1, orient=HORIZONTAL)
        self.scale3.set(1.0)
        self.scale3.pack()

        button = tk.Button(self, text="Go to the start page",
                    command=lambda: controller.show_frame("StartPage"))
        button.pack()
    

class StartPage(PageWeights):

    def __init__(self, parent, controller, page_weights):
        tk.Frame.__init__(self, parent, bg='#3d3d5c')
        self.controller = controller
        self.availabilities_filename = ""
        self.coordinates_filename = ""
        self.output_filename = ""

        self.controller.title('Bene\'s Assignment Program')
        self.controller.geometry('600x600') #self.controller.state('zoomed')

        welcome_label1 = tk.Label(self,
            text = "Welcome to",
            font=('Berlin Sans FB', 12),
            fg='white',
            bg='#3d3d5c')
        welcome_label1.pack(side="top", fill="x", pady=0)

        welcome_label2 = tk.Label(self, 
            text="Benes Assignment Program", 
            font=('Berlin Sans FB', 26),
            fg='white',
            bg='#3d3d5c')
        welcome_label2.pack(side="top", fill="x", pady=0)


        # === LOWER FRAME ===

        lower_frame = tk.Frame(self, bg='#33334d', pady=20)
        lower_frame.pack(fill='both', expand=True)

        def start_computation(weights):
            filenames = [self.availabilities_filename, self.coordinates_filename, self.output_filename]
            if  all(['.xlsx' in file for file in filenames]):
                try:
                    teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments = data.get_problem(self.availabilities_filename, self.coordinates_filename)
                    worst_case_distance = max(1, int(sum([assignment[3] for assignment in pulp.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights=[0,0,-1,0], worst_case_distance=1)[1]])))
                    optimal_found, assignments = pulp.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments, weights, worst_case_distance)
                except Exception as exception:
                    Handle(exception)
                
                if not optimal_found:
                    print("Optimal solution was not found!")
                else:
                    print("Optimal solution found!")
                
                data.write_model(self.output_filename, teachers, events, desired_workdays, event_size, event_durations, assignments, weights, worst_case_distance)
            else:
                print("Not all filenames specified, cannot compute.")
            
            sys.stdout.flush()


        def get_weights():
            lam = 0.4
            return [lam * page_weights.scale1.get(), (1 - lam) * page_weights.scale1.get(), page_weights.scale2.get(), page_weights.scale3.get()]

        compute_button = tk.Button(lower_frame, 
            text='Start computation', 
            bg='green',
            pady=10,
            command=lambda: start_computation(get_weights())
        )

        def place_button_if_ready():
            filenames = [self.availabilities_filename, self.coordinates_filename, self.output_filename]
            if all(['.xlsx' in file for file in filenames]):
                tk.Label(lower_frame, bg='#33334d').pack()  # spaceholder
                compute_button.pack()

        def open_file1():
            browse_input_text.set('Loading...')
            filename = fd.askopenfilename(
                title='Open Availability Sheet',
                initialdir='/',
                filetypes=[('Excel Files','*.xlsx')]
            )
            browse_input_text.set('Open Availabilities Sheet')
            input_text.set('Selected: ' + filename.split('/')[-1])
            self.availabilities_filename = filename
            place_button_if_ready()

        def open_file2():
            browse_input2_text.set('Loading...')
            filename = fd.askopenfilename(
                title='Open Coordinates Sheet',
                initialdir='/',
                filetypes=[('Excel Files','*.xlsx')]
            )
            browse_input2_text.set('Open Coordinates Sheet')
            input2_text.set('Selected: ' + filename.split('/')[-1])
            self.coordinates_filename = filename
            place_button_if_ready()

        def save_file():
            browse_output_text.set('Loading...')
            filename = fd.asksaveasfilename(
                title='Select output file',
                initialdir='/',
                filetypes=[('Excel Files','*.xlsx')]
            )
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            browse_output_text.set('Save to...')
            output_text.set('Selected: ' + filename.split('/')[-1])
            self.output_filename = filename
            place_button_if_ready()

        #input1
        browse_input_text = tk.StringVar()
        input_text = tk.StringVar()

        open_file_button = tk.Button(lower_frame, textvariable=browse_input_text, pady=10, command=open_file1)
        browse_input_text.set('Open Availabilities Sheet')
        open_file_button.pack()
        
        input_text_lbl = tk.Label(lower_frame, textvariable=input_text, bg='#3d3d5c', fg='white')
        input_text.set('No file specified')
        input_text_lbl.pack()
        tk.Label(lower_frame, bg='#33334d').pack()  # spaceholder

        #input2
        browse_input2_text = tk.StringVar()
        input2_text = tk.StringVar()

        open_file_button2 = tk.Button(lower_frame, textvariable=browse_input2_text, pady=10, command=open_file2)
        browse_input2_text.set('Open Coordinates Sheet')
        open_file_button2.pack()
        
        input2_text_lbl = tk.Label(lower_frame, textvariable=input2_text, bg='#3d3d5c', fg='white')
        input2_text.set('No file specified')
        input2_text_lbl.pack()
        tk.Label(lower_frame, bg='#33334d').pack()  # spaceholder

        #output
        browse_output_text = tk.StringVar()
        output_text = tk.StringVar()

        save_to_button = tk.Button(lower_frame, textvariable=browse_output_text, pady=10, command=save_file)
        browse_output_text.set('Save to...')
        save_to_button.pack()

        output_text_lbl = tk.Label(lower_frame, textvariable=output_text, bg='#3d3d5c', fg='white')
        output_text.set('No file specified')
        output_text_lbl.pack()
        
        # === LOWEST FRAME ===

        lowest_frame = tk.Frame(self, bg='#3d3d5c', pady=0)
        lowest_frame.pack(fill='both', expand=True)

        button1 = tk.Button(lowest_frame, 
            text="Custom weights", 
            command=lambda: controller.show_frame("PageWeights"))
        button2 = tk.Button(lowest_frame, 
            text="Help",
            width=10,
            command=lambda: controller.show_frame("PageHelp"))

        button1.grid(row=0, column=0, pady = 50, padx=100, sticky="W")
        button2.grid(row=0, column=1, padx=100, sticky="E")

        lowest_frame.columnconfigure(0, weight=1)
        lowest_frame.rowconfigure(1, weight=1)

class PageHelp(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Help", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        text = Text(self)
        text.pack()

        try:
            with open('README.txt', 'r') as f:
                content = f.read()
        except:
            content = "Was not able to load text. Sorry."
        text.insert('1.0', content)

        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()

def Handle(exception):
    sys.stdout.flush()
    with open(stderr_file_path, 'w') as stderr_file:
            stderr_file.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            stderr_file.write(traceback.format_exc())
            raise(exception)


if __name__ == "__main__":

    stdout_file_path = "logs.txt"
    stderr_file_path = "errors.txt"
    try:
        with open(stdout_file_path, 'w') as stdout_file:
                with redirect_stdout(stdout_file):
                        print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                        print("Starting program...")
                        sys.stdout.flush()

                        app = SampleApp()
                        app.mainloop()

    except Exception as exception:
        Handle(exception)