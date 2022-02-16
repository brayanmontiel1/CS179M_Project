# img_viewer.py

import PySimpleGUI as sg
import os.path


# Button info
FONT = 'Courier'
FONT_SIZE = 10
SELECTED_CHAR = '●'
MAX_ROWS = 12
MAX_COL = 8
table = [[True]*MAX_COL for _ in range(MAX_ROWS)]

sg.change_look_and_feel('Dark Grey 6')

# Start building layout with the top 2 rows that contain Text elements
buttonGridLayout =   [[sg.Text('Unload/Offload', font='Default 25')],
       [sg.Text(size=(15,1), key='-MESSAGE-', font='Default 20')]]
# Add the board, a grid a buttons
buttonGridLayout +=  [[sg.Button(str(SELECTED_CHAR), size=(2,1), pad=(0,0), border_width=0, key=(row,col), font=(FONT,FONT_SIZE)) for col in range(MAX_COL)] for row in range(MAX_ROWS)]
# Add the exit button as the last row
buttonGridLayout +=  [[sg.Button('Exit')]]

# First the window layout in 2 columns

file_list_column = [
    [
        sg.Text("Image Folder"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
        )
    ],
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.Text("Choose an image from list on left:")],
    [sg.Text(size=(40, 1), key="-TOUT-")],
    [sg.Image(key="-IMAGE-")],
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(buttonGridLayout),
    ]
]

window = sg.Window("Image Viewer", layout,resizable=True)

# Run the Event Loop
while True:
    event, values = window.read()

    # File search
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith((".png", ".gif", ".jpeg"))
        ]
        window["-FILE LIST-"].update(fnames)
    elif event == "-FILE LIST-":  # A file was chosen from the listbox
        try:
            filename = os.path.join(
                values["-FOLDER-"], values["-FILE LIST-"][0]
            )
            window["-TOUT-"].update(filename)
            window["-IMAGE-"].update(filename=filename)

        except:
            pass


    # Button Grid
    table[event[0]][event[1]] = not table[event[0]][event[1]]
    window[event].update((' ',SELECTED_CHAR)[table[event[0]][event[1]]] )

window.close()