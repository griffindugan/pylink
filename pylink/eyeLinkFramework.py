"""

Author: Griffin Dugan
Wingfield Lab
Python Eyelink Framework


Description: This file is designed as a framework to build other programs using the EyeLink software allowing for more understandable and readable code.
Mainly is based around the eyeLink class object.

Requires CalibrationGraphicsPygame.py to be in the same folder.

Known Bugs: unsure

"""

import os
import sys
from string import ascii_letters, digits
import time
import pylink
from pylink.CalibrationGraphicsPygame import CalibrationGraphics
import pygame
from pygame.locals import *
import numpy as np
from collections import defaultdict as dd


# colour values
class Colour:
    """Colour handler between name, rgb, and host PC colour

    :ivar name: Name of colour
    :vartype name: str
    :ivar rgb: RGB code for colour
    :vartype rgb: tuple[int, int, int]
    :ivar hostCol: Host PC number for colour
    :vartype hostCol: int
    """
    def __init__(self, name:str, rgb:tuple[int, int, int], hostCol:int) -> None:
        """Colour handler between name, rgb, and host PC colour

        :param name: Name of colour
        :type name: str
        :param rgb: RGB code for colour
        :type rgb: tuple[int, int, int]
        :param hostCol: Host PC number for colour
        :type hostCol: int
        """

        self.name = name
        self.rgb = rgb
        self.host = hostCol
    
BLACK = Colour("BLACK", (0, 0, 0), 0)
BLUE = Colour("BLUE", (50, 50, 255), 1)
GREEN = Colour("GREEN", (50,128,50), 2)
CYAN = Colour("CYAN", (50, 255, 255), 3)
RED = Colour("RED", (255, 50, 50), 4)
VIOLET = Colour("VIOLET", (238,130,238), 5)
BROWN = Colour("BROWN", (139,69,19), 6)
LIGHT_GREY = Colour("LIGHT GREY", (211,211,211), 7)
GREY = Colour("GREY", (128, 128, 128), 8) # "Dark Grey" on host PC
LIGHT_BLUE = Colour("LIGHT BLUE", (135,206,250), 9)
LIME = Colour("LIME", (50,255,50), 10)
LIGHT_CYAN = Colour("LIGHT CYAN", (200,255,255), 11)
PINK = Colour("PINK", (255,192,203), 12)
MAGENTA = Colour("MAGENTA", (255,50,255), 13)
YELLOW = Colour("YELLOW", (255,255,50), 14)
WHITE = Colour("WHITE", (255, 255, 255), 15)
COLOURS = [BLACK, BLUE, GREEN, CYAN, RED, VIOLET, BROWN, LIGHT_GREY, GREY, LIGHT_BLUE, LIME, LIGHT_CYAN, PINK, MAGENTA, YELLOW, WHITE]

def findColour(name:str, colours:list[Colour]=COLOURS) -> Colour:
    for colour in colours:
        if colour.name == name:
            return colour
    return None  # Return None if no match is found


def init_files(results_folder:str="results") -> tuple[str, str]:
    """Creates the folders and initialises the files.

    :param results_folder: Results folder name, defaults to "results"
    :type results_folder: str, optional
    :return: Returns the name of the EDF file created as well as the session identifier code.
    :rtype: tuple, (name of EDF file, session identifier)
    """
    # define the script path folder, and switch to it.
    script_path = os.path.dirname(sys.argv[0])
    if len(script_path) != 0:
        os.chdir(script_path)

    # define edf file
    # file has to be less than 8 characters and use only numbers, letters and underscores.
    edf_fname = "TEST"

    # Prompt user to specify an EDF data filename before opening a fullscreen window
    while True:
        prompt = "\nSpecify an EDF filename\n" + \
            "Filename must not exceed eight alphanumeric characters.\n" + \
            "ONLY letters, numbers and underscore are allowed.\n\n--> "
        edf_fname = input(prompt)
        # strip trailing characters, ignore the '.edf' extension
        edf_fname = edf_fname.rstrip().split(".")[0]

        # check if the filename is valid (length <= 8 & no special char)
        allowed_char = ascii_letters + digits + "_"
        if not all([c in allowed_char for c in edf_fname]):
            print("ERROR: Invalid EDF filename")
        elif len(edf_fname) > 8:
            print("ERROR: EDF filename should not exceed 8 characters")
        else:
            break

    # define results folder for EDF file storage, as well as interest areas
    if not os.path.exists(results_folder):
        makeFolder(results_folder)

    # current session ID
    # session identifier is EDFNAME_YEAR_MONTH_DAY_HOUR_MINUTE
    # hours are in 24hr format
    time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
    session_identifier = edf_fname + time_str

    # create the testing session folder
    session_folder = os.path.join(results_folder, session_identifier)
    if not os.path.exists(session_folder):
        makeFolder(session_folder)

    # aoi folder -- this holds VFRAME commands, like interest areas
    aoi_folder = os.path.join(session_folder, "aoi")
    if not os.path.exists(aoi_folder):
        makeFolder(aoi_folder)
    return edf_fname, session_identifier

def makeFolder(path:str) -> None:
    """Makes a folder at the path.

    :param path: The path to where the folder should be made.
    :type path: str
    """
    os.makedirs(path)

class eyeLink:
    """
    EyeLink object handler.

    :ivar id: The session identifier for the particular participant
    :vartype id: str
    :ivar address: IP address of the host PC, if not eye tracking, leave blank, defaults to "None"
    :vartype address: str, optional
    :ivar folders: Folder names, if any are irregular, defaults to {}
    :vartype folders: dict, optional
    :ivar et: The EyeLink object
    :vartype et: object (EyeLink)
    :ivar dm: Whether dummy mode is active or not
    :vartype dm: bool
    :ivar file: The EDF file that the EyeLink stores its data
    :vartype file: str
    :ivar version: The EyeLink tracker version
    :vartype version: str
    :ivar win: The display PC experiment window
    :vartype win: object (eyeLink.window)
    :ivar genv: The host PC window
    :vartype genv: object (CalibrationGraphics)

    ## Methods

    .. autosummary::
       :toctree:

       connect
       configure
       init_calibration
       calibrate
       driftCheck
       terminate
       start_trial
       record
       create_ia
       stopRecording
       drawHostLine
       clearHostScreen
       clearDVScreen
       checkDisconnect

    """
    def __init__(self, id:str, address:str="None", folders:dict={}) -> None:
        """EyeLink object handler

        If using not connecting to an eyetracker, use address '"None"'.

        :param id: The session identifier for the particular participant
        :type id: str
        :param address: IP address of the host PC, if not eye tracking, defaults to "None"
        :type address: str, optional
        :param folders: Folder names, if any are irregular, defaults to {}
        :type folders: dict, optional
        """
        # Define from Parameters 
        self.id = id
        self.address = address

        # Set default values for folders
        self.folders = {
            "m"  : os.path.dirname(sys.argv[0]),        # main folder
            "f"  : "TEST",                              # file name
            "r"  : "results",                           # results folder
            "s"  : os.path.join("results", id),         # session folder
            "aoi": os.path.join("results", id, "aoi")   # aoi folder
        }
        
        # Define folder names as given, if given
        for key, path in folders.items():
            self.folders[key] = path
        
        # Connect to EyeLink
        self.connect()

        # Configure EyeLink
        self.configure()

        

    def connect(self, address:str="Default") -> None:
        """Connects to the EyeLink using the address defined in initialisation, or to the address included here.

        If using not connecting to an eyetracker, use address '"None"'.

        :param address: A different IP address of host computer if not previously defined, defaults to "Default"
        :type address: str, optional
        """
        # If an addresds is provided here, switch to that address
        if address != "Default": self.address = address

        # For no Eye Tracker mode, use "None"
        if self.address == "None":
            self.et = pylink.EyeLink(None) # Defines EyeLink
            self.dm = True # Sets dummymode to true.
        else:
            try:
                self.et = pylink.EyeLink(self.address) # Defines EyeLink
                self.dm = False # Sets dummymode to off
            except RuntimeError as error: # If error ocurs when trying to connect (usually address not accessible)
                print("ERROR:", error)
                pygame.quit()
                sys.exit()

        # Open an EDF data file on the Host PC
        self.file = self.folders["f"] + ".EDF" 
        try:
            self.et.openDataFile(self.file) # Creates the file on the Host PC
        except RuntimeError as err:
            print("ERROR:", err)
            # close the link if we have one open
            if self.et.isConnected():
                self.et.close()
            pygame.quit()
            sys.exit()

        # Add a header text to the EDF file to identify the current experiment name
        # Allows data viewer to see a header.
        preamble_text = f"RECORDED BY {os.path.basename(__file__)}"
        self.et.sendCommand(f"add_file_preamble_text '{preamble_text}'")

    def configure(self, sample_rate:int=None, calibration_type:str="HV9") -> None:
        """Configures the eye tracker.

        :param sample_rate: If you need a specific sample rate, you can add one, defaults to None
        :type sample_rate: int, optional
        :param calibration_type: If you need a calibration type outside of the normal, you can change it, defaults to "HV9"
        :type calibration_type: str, optional
        """
        # Put the tracker in offline mode before changing tracking parameters
        self.et.setOfflineMode()

        # Get the software version:  
        # Options: 1: EyeLink I, 2: EyeLink II, 3/4: EyeLink 1000, 5: EyeLink 1000 Plus, 6: Portable DUO
        self.version = 0  # set version to 0, in case running in Dummy mode
        if not self.dm:
            vstr = self.et.getTrackerVersionString()
            self.version = int(vstr.split()[-1].split(".")[0]) # get only the first number
            # print out some version info in the shell
            print(f"Running experiment on {vstr}, version {self.version}")

        
        # File and Link data control
        #   These are the data events that the tracker can track.
        #   By default, set to all.

        # what eye events to save in the EDF file, include everything by default
        file_event_flags = "LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT"
        # what eye events to make available over the link, include everything by default
        link_event_flags = "LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT"
        
        # what sample data to save in the EDF data file and to make available over the link, include the 'HTARGET' flag to save head target sticker
        #  data for supported eye trackers
        if self.version > 3: # depends based on type of tracker
            file_sample_flags = "LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT"
            link_sample_flags = "LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT"
        else:
            file_sample_flags = "LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT"
            link_sample_flags = "LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT"
        self.et.sendCommand(f"file_event_filter = {file_event_flags}")
        self.et.sendCommand(f"file_sample_data = {file_sample_flags}")
        self.et.sendCommand(f"link_event_filter = {link_event_flags}")
        self.et.sendCommand(f"link_sample_data = {link_sample_flags}")

        # If you need special a special sample rate:
        #   Sample rate: 250, 500, 1000, or 2000 -- depends on tracker, check your tracker specification
        if sample_rate:
            self.et.sendCommand(f"sample_rate {sample_rate}")        

        # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
        self.et.sendCommand(f"calibration_type = {calibration_type}")

        # Set a gamepad button to accept calibration/drift check target
        #   You need a supported gamepad/button box that is connected to the Host PC
        self.et.sendCommand("button_function 5 'accept_target_fixation'")

    def init_calibration(self, 
                         fullscreen:bool, 
                         screensize:tuple[int, int], 
                         genv_fg:tuple[int, int, int]=BLACK.rgb, 
                         genv_bg:tuple[int, int, int]=GREY.rgb,
                         calibration_target:str="circle",
                         picture_target:str=None,
                         target_size:int=24,
                         calibration_sound:bool=False,
                         sounds:list[str, str, str]=None) -> None:
        """Initialises the EyeLink calibration setup. Creates the pygame window.

        :param fullscreen: Whether the window on Display PC should be fullscreen.
        :type fullscreen: bool
        :param screensize: If not full screen, determine the screen size.
        :type screensize: tuple[int, int]

        :param genv_fg: Base environment text colour, defaults to BLACK
        :type genv_fg: tuple[int, int, int], optional
        :param genv_bg: Base environment background colour, defaults to GREY
        :type genv_bg: tuple[int, int, int], optional
        :param calibration_target: Calibration target shape, defaults to "circle"
        :type calibration_target: str, optional
        :param picture_target: If there's a picture target, add the path, defaults to None
        :type picture_target: str, optional
        :param target_size: Calibration target size (in pixels), defaults to 24
        :type target_size: int, optional
        :param calibration_sound: Whether the calibration should make sound, defaults to False
        :type calibration_sound: bool, optional
        :param sounds: If you want custom sounds, outside of default, add a list of 3 .wav file paths, defaults to None
        :type sounds: list[str, str, str], optional
        """
        # Defining PyGame Window
        self.win = self.window(parent=self, fullscreen=fullscreen, screensize=screensize)

        pygame.mouse.set_visible(False)  # hide mouse cursor

        # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
        #   see the EyeLink Installation Guide, "Customizing Screen Settings"
        el_coords = f"screen_pixel_coords = 0 0 {self.win.width - 1} {self.win.height - 1}"
        self.et.sendCommand(el_coords)

        # Write a DISPLAY_COORDS message to the EDF file
        # Data Viewer needs this piece of info for proper visualization, 
        #   see Data Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        dv_coords = f"DISPLAY_COORDS  0 0 {self.win.width - 1} {self.win.height - 1}"
        self.et.sendMessage(dv_coords)

        # Configure a graphics environment (genv) for tracker calibration
        self.genv = CalibrationGraphics(self.et, self.win.dis)

        # Set background and foreground colors
        #   parameters: foreground_color, background_color
        self.genv.setCalibrationColors(genv_fg, genv_bg)


        # Set up the calibration target

        # The target could be a "circle" (default) or a "picture",
        # To configure the type of calibration target, set
        # genv.setTargetType to "circle", "picture", e.g.,
        # genv.setTargetType('picture')

        # Use gen.setPictureTarget() to set a "picture" target, e.g.,
        # genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))

        # Use the default calibration target
        self.genv.setTargetType(calibration_target)
        if calibration_target == "picture": # If the calibration target is a picture.
            try:
                self.genv.setPictureTarget(picture_target)
            except: 
                print(f"The path ({picture_target}) did not lead to a valid calibration target.")

        # Configure the size of the calibration target (in pixels)
        self.genv.setTargetSize(target_size)

        # Beeps to play during calibration, validation and drift correction
        # parameters: target, good, error
        #     target -- sound to play when target moves
        #     good -- sound to play on successful operation
        #     error -- sound to play on failure or interruption
        # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
        # e.g., genv.setCalibrationSounds('type.wav', 'qbeep.wav', 'error.wav')
        if calibration_sound:
            if sounds: self.genv.setCalibrationSounds(*sounds) # Granted, I am unsure that this will work correctly.
            else: self.genv.setCalibrationSounds("","","")
        else: self.genv.setCalibrationSounds("off", "off", "off")

        # Request Pylink to use the Pygame window we opened above for calibration
        pylink.openGraphicsEx(self.genv)

    def calibrate(self, 
                  task_msg:str, 
                  fg_colour:tuple[int, int, int]=BLACK.rgb, 
                  bg_colour:tuple[int, int, int]=GREY.rgb, 
                  task_key:list=[K_RETURN]) -> None:
        """Calibrates the tracker.

        :param task_msg: Display message for the task instructions.
        :type task_msg: str

        :param fg_colour: Task message text colour, defaults to BLACK
        :type fg_colour: tuple[int, int, int], optional
        :param bg_colour: Task message background colour, defaults to GREY
        :type bg_colour: tuple[int, int, int], optional
        :param task_key: Task message begin key, defaults to RETURN/ENTER key
        :type task_key: list, optional
        """
        # Show task message and wait for task key to be pressed
        self.win.show_message(task_msg, fg_colour, bg_colour)
        self.win.wait_key(task_key)

        # skip if running in Dummy Mode
        if not self.dm:
            try:
                self.et.doTrackerSetup() # Calibrate
            except RuntimeError as err:
                print("ERROR:", err)
                self.et.exitCalibration()

    class window:
        """EyeLink Display PC window object manager.

        :ivar parent: The eyeLink class object that the window is managed by.
        :vartype parent: eyeLink object
        :ivar fullscreen: Whether the window should be full screen.
        :vartype fullscreen: bool
        :ivar screensize: If not full screen, determines the screen size.
        :vartype screensize: tuple
        :ivar width: The width of the screen
        :vartype width: int
        :ivar height: The height of the screen
        :vartype height: int
        :ivar et: The EyeLink tracker object from the eyeLink parent object.
        :vartype et: EyeLink object
        :ivar dis: The pygame display surface
        :vartype dis: Surface
        :ivar surf: Possibly the same as dis # TODO: figure out
        :vartype surf: Surface
    
        ## Methods

        .. autosummary::
        :toctree:

            show_message
            wait_key
            abort

        """
        def __init__(self, parent, fullscreen:bool, screensize:tuple) -> None:
            """EyeLink Display PC window object manager.

            :param parent: The eyeLink class object that the window is managed by.
            :type parent: eyeLink object
            :param fullscreen: Whether the window should be full screen.
            :type fullscreen: bool
            :param screensize: If not full screen, determines the screen size.
            :type screensize: tuple
            """
            self.fullscreen = fullscreen
            self.screensize = (self.width, self.height) = screensize
            self.parent = parent
            self.et = parent.et
            
            self.dis = None # Set display to none to begin
            if self.fullscreen:
                self.dis = pygame.display.set_mode((0, 0), FULLSCREEN | DOUBLEBUF) # define it as doublebuf-ed full screen
                self.screensize = self.width, self.height = self.dis.get_size() # Reset the size based on full screen size
            else:
                self.dis = pygame.display.set_mode(self.screensize, 0) # define it based on set screen size
                # TODO: doublebuf?

                pygame.display.set_caption("EVE") # Set heading
            
            # TODO: also maybe check to see if the screen size is bigger than the screen?

            self.surf = pygame.display.get_surface() # Defining the surface
            # TODO: is this necessary?

        def show_message(self, 
                         message:str, 
                         fg_colour:tuple[int, int, int], 
                         bg_colour:tuple[int, int, int], 
                         font:str="Arial", 
                         font_size:int=32) -> None:
            """Show messages on the display PC screen

            :param message: The message you would like to show
            :type message: str
            :param fg_colour: RGB text colour
            :type fg_colour: tuple[int, int, int]
            :param bg_colour: RGB background colour
            :type bg_colour: tuple[int, int, int]
            :param font: Font of message, defaults to "Arial"
            :type font: str, optional
            :param font_size: Font size of message, defaults to 32
            :type font_size: int, optional
            """
            # clear the screen
            self.surf.fill(bg_colour)

            message_fnt = pygame.font.SysFont(font, font_size) 
            msgs = message.split("\n")
            for i in range(len(msgs)): # TODO: I can't help but feel there might be a better way to do this.
                message_surf = message_fnt.render(msgs[i], True, fg_colour)
                w, h = message_surf.get_size()
                msg_y = self.height / 2 + h / 2 * 2.5 * (i - len(msgs) / 2.0)
                self.surf.blit(message_surf, (int(self.width / 2 - w / 2), int(msg_y)))

            pygame.display.flip()

        def wait_key(self, key_list:list, duration:int=sys.maxsize) -> list:
            """Detect and return a keypress, terminate the task if ESCAPE is pressed

            :param key_list: Allowable keys (pygame key constants, e.g., [K_a, K_ESCAPE]
            :type key_list: list
            :param duration: the maximum time allowed to issue a response (in ms). Wait for response 'indefinitely' (with sys.maxsize), defaults to sys.maxsize
            :type duration: int, optional
            :return: Pressed key names
            :rtype: list
            """
            parent = self.parent # easy defining

            got_key = False
            # clear all cached events if there are any
            pygame.event.clear()
            t_start = pygame.time.get_ticks()
            resp = [None, t_start, -1]

            while not got_key:
                # check for time out
                if (pygame.time.get_ticks() - t_start) > duration:
                    break

                # check key presses
                for ev in pygame.event.get():
                    if ev.type == KEYDOWN:
                        if ev.key in key_list:
                            resp = [pygame.key.name(ev.key),
                                    t_start,
                                    pygame.time.get_ticks()]
                            got_key = True

                    # on esc, terminate task
                    if (ev.type == KEYDOWN) and (ev.key == K_ESCAPE):
                        parent.terminate()

            # clear the screen following each keyboard response
            win_surf = pygame.display.get_surface()
            win_surf.fill(parent.genv.getBackgroundColor())
            pygame.display.flip()

            return resp

        def abort(self, bg_colour:tuple[int, int, int]=GREY.rgb) -> any:
            """Ends recording. 100 msec are added to catch final events.

            :param bg_colour: RGB background colour, defaults to GREY
            :type bg_colour: tuple[int, int, int], optional

            :return: Trial Errort
            :rtype: pylink.TRIAL_ERROR
            """
            # TODO: abort could possibly be in eyeLink, not window, but eh
            # get the currently active tracker object (connection)
            # TODO: TEST WITH TRACKER FOR NECESSITY
            if not self.parent.dm:
                et = pylink.getEYELINK()
                if et != self.et: print("trackers not the same?")

                # Stop recording
                if self.et.isRecording():
                    # add 100 ms to catch final trial events
                    pylink.pumpDelay(100)
                    self.et.stopRecording()

                # Send a message to clear the Data Viewer screen
                self.parent.clearDVScreen(colour=bg_colour)

                # send a message to mark trial end
                self.et.sendMessage(f"TRIAL_RESULT {pylink.TRIAL_ERROR}")

            # clear the screen
            surf = pygame.display.get_surface()
            surf.fill(bg_colour)
            pygame.display.flip()

            return pylink.TRIAL_ERROR

    def driftCheck(self, 
                   dc_x:int, dc_y:int, 
                   bgColour:tuple[int, int, int]=GREY.rgb, 
                   circleColour:tuple[int, int, int]=RED.rgb, 
                   circleRad:int=10) -> any:
        """Performs a drift check.

        :param dc_x: Drift correct circle x position
        :type dc_x: int
        :param dc_y: Drift correct circle y position
        :type dc_y: int
        :param bgColour: RGB Background colour, defaults to GREY
        :type bgColour: tuple[int, int, int], optional
        :param circleColour: RGB circle colour, defaults to RED
        :type circleColour: tuple[int, int, int], optional
        :param circleRad: Radius of circle, defaults to 10
        :type circleRad: int, optional
        :return: Only returns if tracker no longer connected
        :rtype: None or pylink.ABORT_EXPT
        """
        while not self.dm: # only drift check when not in dummymode
            surf = self.win.surf 

            # terminate the task if no longer connected to the tracker or user pressed Ctrl-C to terminate the task
            if (not self.et.isConnected()) or self.et.breakPressed():
                self.terminate()
                return pylink.ABORT_EXPT

            # draw a custom drift-correction target;
            surf.fill(bgColour)
            pygame.draw.circle(surf, circleColour, (int(dc_x), int(dc_y)), circleRad)
            pygame.display.flip()
            # drift-check and re-do camera setup if ESCAPE is pressed
            try:
                error = self.et.doDriftCorrect(int(dc_x), int(dc_y), 0, 1)
                # break following a success drift-check
                if error is not pylink.ESC_KEY:
                    break
            except:
                pass
    
    def terminate(self, 
                  fg_colour:tuple[int, int, int]=BLACK.rgb, 
                  bg_colour:tuple[int, int, int]=GREY.rgb) -> None:
        """Terminate the task safely and retrieve the EDF data file.

        :param fg_colour: Transfer text colour, defaults to BLACK
        :type fg_colour: tuple[int, int, int], optional
        :param bg_colour: Transfer background colour, defaults to GREY
        :type bg_colour: tuple[int, int, int], optional
        """
        # disconnect from the tracker if there is an active connection
        if not self.dm:
            et = pylink.getEYELINK() # TODO: TEST WITH TRACKER FOR NECESSITY
            if et != self.et: print("trackers not the same?")

            if self.et.isConnected(): # if it's not connected, not necessary
                # Terminate the current trial first if the task terminated prematurely
                error = self.et.isRecording()
                if error == pylink.TRIAL_OK:
                    self.win.abort()

                self.et.setOfflineMode() # Put tracker in Offline mode

                # Clear the Host PC screen and wait for 500 ms
                self.clearHostScreen(BLACK.host)
                pylink.msecDelay(500)

                self.et.closeDataFile() # Close the edf data file on the Host PC

                # Show a file transfer message on the screen
                msg = "EDF data is transferring from EyeLink Host PC..."
                self.win.show_message(msg, fg_colour, bg_colour)

                # Download the EDF data file from the Host PC to a local data folder
                # parameters: source_file_on_the_host, destination_file_on_local_drive
                local_edf = os.path.join(self.folders["s"], self.id + ".EDF")
                try:
                    self.et.receiveDataFile(self.folders["f"], local_edf)
                except RuntimeError as error:
                    print("ERROR:", error)

                self.et.close() # Close the link to the tracker.

        # quit pygame and python
        pygame.quit()
        sys.exit()

    def start_trial(self, trial_index:int, condition:str) -> None:
        """Start a trial with the EyeLink Host PC

        :param trial_index: Trial Index number
        :type trial_index: int
        :param condition: Trial Condition label
        :type condition: str
        """
        self.et.setOfflineMode() # put the tracker in the offline mode first

        # send a "TRIALID" message to mark the start of a trial, 
        #   see Data Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        self.et.sendMessage(f"TRIALID {trial_index}")

        # record_status_message : show some info on the Host PC
        # here we show how many trial has been tested
        status_msg = f"TRIAL number {trial_index}, {condition}"
        self.et.sendCommand(f"record_status_message '{status_msg}'")

    def record(self) -> any:
        """Begin the EyeTracker recording

        :return: Nothing or pylink.TRIAL_ERROR if runtime error
        :rtype: None or pylink.TRIAL_ERROR
        """
        self.et.setOfflineMode() # put tracker in idle/offline mode before recording

        # Start recording
        #   arguments: sample_to_file, events_to_file, sample_over_link, event_over_link (1-yes, 0-no)
        try:
            self.et.startRecording(1, 1, 1, 1)
        except RuntimeError as error:
            print("ERROR:", error)
            self.win.abort()
            return pylink.TRIAL_ERROR

        pylink.pumpDelay(100) # Allocate some time for the tracker to cache some samples

    def create_ia(self, trial_index:int, msg:str, newTrial:bool=False) -> None:
        """Creates an interest area file.

        :param trial_index: The trial index number
        :type trial_index: int
        :param msg: The message to write to file
        :type msg: str
        :param newTrial: If a new trial has started create the file, otherwise just open and add, defaults to False
        :type newTrial: bool, optional
        """
        # open a INTEREST AREA SET file to make a dynamic IA for the target
        if newTrial:
            ias = f"IA_{trial_index}.ias"
            ias_path = os.path.join(self.folders["aoi"], ias)
            self.folders["ias"] = ias_path
            self.et.sendMessage(f"!V IAREA FILE {ias_path}")
            self.ias_file = open(self.folders["ias"], "w")
        self.ias_file.write(msg)

    def stopRecording(self, trial_info:list, trial_labels:list=None) -> None:
        """Stops recording, and uploads trial info to EDF file.

        :param trial_info: Trial info for EDF file.
        :type trial_info: list
        :param trial_labels: List of data for the trials, defaults to None
        :type trial_labels: list, optional
        """
        self.ias_file.close() # close the IAS file that contains the dynamic IA definition

        # stop recording; add 100 msec to catch final events before stopping
        pylink.pumpDelay(100)
        self.et.stopRecording()

        # record trial variables to the EDF data file, for details, 
        #   see Data Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        for message in trial_info:
            self.et.sendMessage(message)
            pylink.msecDelay(4)

        if trial_labels:
            self.et.sendMessage(f"!V TRIAL_VAR_DATA {trial_labels}")

        
        # send a 'TRIAL_RESULT' message to mark the end of trial, 
        #   see Data Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        self.et.sendMessage(f"TRIAL_RESULT {pylink.TRIAL_OK}")
        
    def drawHostLine(self, pos1:tuple[int, int], pos2:tuple[int, int], colour:str) -> None:
        """Draws a line on the Host PC between two positions

        :param pos1: Position 1 (x, y)
        :type pos1: tuple[int, int]
        :param pos2: Position 2 (x, y)
        :type pos2: tuple[int, int]
        :param colour: The line colour (see below for valid options), must be all caps
        :type colour: str

        The color codes supported on the Host PC:
         - BLACK
         - BLUE
         - GREEN
         - CYAN
         - RED
         - VIOLET
         - BROWN
         - LIGHT GREY
         - GREY
         - LIGHT BLUE
         - LIME
         - LIGHT CYAN
         - PINK
         - MAGENTA
         - YELLOW
         - WHITE
        see /elcl/exe/COMMANDs.INI on the Host
        """
        col = findColour(colour)
        if col: self.et.sendCommand("draw_line {} {} {} {} {}".format(*pos1, *pos2, col.host))
        else: print(f"No colour was found with name '{colour}'. Please check documentation for clearHostScreen()." if col == None else f"The host PC could not find colour id {col}, name {colour}. Please check documentation for clearHostScreen().")
        
    def clearHostScreen(self, colour:str="BLACK") -> None:
        """Clears the Host PC's screen

        :param colour: The screen colour (see below for valid options), defaults to BLACK
        :type colour: str, optional

        The color codes supported on the Host PC:
         - BLACK
         - BLUE
         - GREEN
         - CYAN
         - RED
         - VIOLET
         - BROWN
         - LIGHT GREY
         - GREY
         - LIGHT BLUE
         - LIME
         - LIGHT CYAN
         - PINK
         - MAGENTA
         - YELLOW
         - WHITE
        see /elcl/exe/COMMANDs.INI on the Host
        """
        col = findColour(colour)
        if col: self.et.sendCommand(f"clear_screen {col.host}")
        else: print(f"No colour was found with name '{colour}'. Please check documentation for clearHostScreen()." if col == None else f"The host PC could not find colour id {col}, name {colour}. Please check documentation for clearHostScreen().")
                            
    def clearDVScreen(self, colour:tuple[int,int,int]=GREY.rgb) -> None:
        """Tells DataViewer to clear the screen.

        :param colour: RGB cleared screen colour, defaults to GREY
        :type colour: tuple[int,int,int], optional
        """
        self.et.sendMessage("blank_screen")
        self.et.sendMessage("!V CLEAR {} {} {}".format(*colour))

    def checkDisconnect(self) -> bool:
        """Checks if the EyeLink has diconnected.

        :return: If the EyeLink is disconnected.
        :rtype: bool
        """
        error = self.et.isRecording()
        if error is not pylink.TRIAL_OK:
            self.et.sendMessage("tracker_disconnected")
            self.win.abort()
            self.error = error
            return True
        else: return False













