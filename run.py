import tkinter as tk
from tkinter import font  as tkfont
from tkinter import filedialog as fd

import data
import compute_pulp

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
        for F in (StartPage, PageOne, PageTwo):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):


    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg='#3d3d5c')
        self.controller = controller

        self.availabilities_filename = ""
        self.coordinates_filename = ""
        self.output_filename = ""


        self.controller.title('Benes Assignment Program')
        self.controller.geometry('600x500') #self.controller.state('zoomed')

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

        def compute(weights):
            filenames = [self.availabilities_filename, self.coordinates_filename, self.output_filename]
            if  all(['.xlsx' in file for file in filenames]):
                teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments = data.get_problem(self.availabilities_filename, self.coordinates_filename)
                optimal_found, assignments = compute_pulp.compute_optimum(teachers, events, event_overlap_sets, desired_workdays, event_size, event_durations, possible_assignments)
                
                if not optimal_found:
                    print("Optimal solution was not found!")
                
                data.write_model(self.output_filename, teachers, events, desired_workdays, event_size, event_durations, assignments)
            else:
                print("Not all filenames specified, cannot compute.")

        compute_button = tk.Button(lower_frame, 
            text='Start computation', 
            bg='green',
            pady=10,
            command=lambda: compute([1,1,1,1])
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

        button1 = tk.Button(lowest_frame, text="Go to Page One",
                    command=lambda: controller.show_frame("PageOne"))
        button2 = tk.Button(lowest_frame, text="Go to Page Two",
                            command=lambda: controller.show_frame("PageTwo"))
        button1.grid(row=0, column=0, pady = 50, padx=100)
        button2.grid(row=0, column=1, padx = 10)





class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 1", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 2", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()