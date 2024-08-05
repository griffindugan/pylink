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
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
GREY = (128, 128, 128)


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
    edf_fname = 'TEST'

    # Prompt user to specify an EDF data filename before opening a fullscreen window
    while True:
        prompt = '\nSpecify an EDF filename\n' + \
            'Filename must not exceed eight alphanumeric characters.\n' + \
            'ONLY letters, numbers and underscore are allowed.\n\n--> '
        edf_fname = input(prompt)
        # strip trailing characters, ignore the '.edf' extension
        edf_fname = edf_fname.rstrip().split('.')[0]

        # check if the filename is valid (length <= 8 & no special char)
        allowed_char = ascii_letters + digits + '_'
        if not all([c in allowed_char for c in edf_fname]):
            print('ERROR: Invalid EDF filename')
        elif len(edf_fname) > 8:
            print('ERROR: EDF filename should not exceed 8 characters')
        else:
            break

    # define results folder for EDF file storage, as well as interest areas
    if not os.path.exists(results_folder):
        makeFolder(results_folder)

    # current testing session folder
    # session identifier is EDFNAME_YEAR_MONTH_DAY_HOUR_MINUTE
    # hours are in 24hr format
    time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
    session_identifier = edf_fname + time_str

    # create the folder
    session_folder = os.path.join(results_folder, session_identifier)
    if not os.path.exists(session_folder):
        makeFolder(session_folder)

    # aoi folder -- this holds VFRAME commands, like interest areas
    aoi_folder = os.path.join(session_folder, 'aoi')
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
            "m"  : os.path.dirname(sys.argv[0]), # main folder
            "f"  : "TEST", # file name
            "r"  : "results", # results folder
            "s"  : os.path.join("results", id), # session folder
            "aoi": os.path.join("results", id, "aoi") # aoi folder
        }
        
        # Define folder names as given
        for key, path in folders.items():
            self.folders[key] = path
        
        # Connect to EyeLink
        self.connect()

        # Configure EyeLink
        self.configure()

        

    def connect(self, address:str="Default") -> None:
        """Connects to the EyeLink using the address defined in initialisation, or to the address included here.

        :param address: A different IP address of host computer if not previously defined, defaults to "Default"
        :type address: str, optional
        """
        if address != "Default": self.address = address

        if self.address == "None":
            self.et = pylink.EyeLink(None)
            self.dm = True
        else:
            try:
                self.et = pylink.EyeLink(self.address)
                self.dm = False
            except RuntimeError as error:
                print('ERROR:', error)
                pygame.quit()
                sys.exit()

        # Step 2: Open an EDF data file on the Host PC
        self.file = self.folders["f"] + ".EDF"
        try:
            self.et.openDataFile(self.file)
        except RuntimeError as err:
            print('ERROR:', err)
            # close the link if we have one open
            if self.et.isConnected():
                self.et.close()
            pygame.quit()
            sys.exit()

        # Add a header text to the EDF file to identify the current experiment name
        # This is OPTIONAL. If your text starts with "RECORDED BY " it will be
        # available in DataViewer's Inspector window by clicking
        # the EDF session node in the top panel and looking for the "Recorded By:"
        # field in the bottom panel of the Inspector.
        preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
        self.et.sendCommand("add_file_preamble_text '%s'" % preamble_text)

    def configure(self) -> None:
        """Configures the eye tracker.
        """
        # Step 3: Configure the tracker
        #
        # Put the tracker in offline mode before we change tracking parameters
        self.et.setOfflineMode()

        # Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
        # 5-EyeLink 1000 Plus, 6-Portable DUO
        self.version = 0  # set version to 0, in case running in Dummy mode
        if not self.dm:
            vstr = self.et.getTrackerVersionString()
            self.version = int(vstr.split()[-1].split('.')[0])
            # print out some version info in the shell
            print('Running experiment on %s, version %d' % (vstr, self.version))


        # File and Link data control
        # what eye events to save in the EDF file, include everything by default
        file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
        # what eye events to make available over the link, include everything by default
        link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
        # what sample data to save in the EDF data file and to make available
        # over the link, include the 'HTARGET' flag to save head target sticker
        # data for supported eye trackers
        if self.version > 3:
            file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
            link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
        else:
            file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
            link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
        self.et.sendCommand("file_event_filter = %s" % file_event_flags)
        self.et.sendCommand("file_sample_data = %s" % file_sample_flags)
        self.et.sendCommand("link_event_filter = %s" % link_event_flags)
        self.et.sendCommand("link_sample_data = %s" % link_sample_flags)

        # Optional tracking parameters
        # Sample rate, 250, 500, 1000, or 2000, check your tracker specification
        # if eyelink_ver > 2:
        #     el_tracker.sendCommand("sample_rate 1000")
        # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
        self.et.sendCommand("calibration_type = HV9")
        # Set a gamepad button to accept calibration/drift check target
        # You need a supported gamepad/button box that is connected to the Host PC
        self.et.sendCommand("button_function 5 'accept_target_fixation'")

    def init_calibration(self, fullscreen:bool, screensize:tuple) -> None:
        """Initialises the EyeLink calibration setup. Creates the pygame window.

        :param fullscreen: Whether the window on Display PC should be fullscreen.
        :type fullscreen: bool
        :param screensize: If not full screen, determine the screen size.
        :type screensize: tuple
        """
        self.win = self.window(parent=self, fullscreen=fullscreen, screensize=screensize)

        pygame.mouse.set_visible(False)  # hide mouse cursor

        # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
        # see the EyeLink Installation Guide, "Customizing Screen Settings"
        el_coords = "screen_pixel_coords = 0 0 %d %d" % (self.win.width - 1, self.win.height - 1)
        self.et.sendCommand(el_coords)

        # Write a DISPLAY_COORDS message to the EDF file
        # Data Viewer needs this piece of info for proper visualization, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (self.win.width - 1, self.win.height - 1)
        self.et.sendMessage(dv_coords)

        # Configure a graphics environment (genv) for tracker calibration
        self.genv = CalibrationGraphics(self.et, self.win.dis)

        # Set background and foreground colors
        # parameters: foreground_color, background_color
        foreground_color = (0, 0, 0)
        background_color = (128, 128, 128)
        self.genv.setCalibrationColors(foreground_color, background_color)


        # Set up the calibration target
        #
        # The target could be a "circle" (default) or a "picture",
        # To configure the type of calibration target, set
        # genv.setTargetType to "circle", "picture", e.g.,
        # genv.setTargetType('picture')
        #
        # Use gen.setPictureTarget() to set a "picture" target, e.g.,
        # genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))

        # Use the default calibration target
        self.genv.setTargetType('circle')

        # Configure the size of the calibration target (in pixels)
        self.genv.setTargetSize(24)


        # Beeps to play during calibration, validation and drift correction
        # parameters: target, good, error
        #     target -- sound to play when target moves
        #     good -- sound to play on successful operation
        #     error -- sound to play on failure or interruption
        # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
        # e.g., genv.setCalibrationSounds('type.wav', 'qbeep.wav', 'error.wav')
        self.genv.setCalibrationSounds('off', 'off', 'off')

        # Request Pylink to use the Pygame window we opened above for calibration
        pylink.openGraphicsEx(self.genv)

    def calibrate(self, task_msg:str) -> None:
        """Calibrates the tracker.

        :param task_msg: Display message for the task instructions.
        :type task_msg: str
        """
        # Step 5: Set up the camera and calibrate the tracker
        # Pygame bug warning
        pygame_warning = '\n\nDue to a bug in Pygame 2, the window may have lost' + \
                        '\nfocus and stopped accepting keyboard inputs.' + \
                        '\nClicking the mouse helps get around this issue.'
        if pygame.__version__.split('.')[0] == '2':
            task_msg = task_msg + pygame_warning

        self.win.show_message(task_msg, (0, 0, 0), (128, 128, 128))
        self.win.wait_key([K_RETURN])

        # skip this step if running the script in Dummy Mode
        if not self.dm:
            try:
                self.et.doTrackerSetup()
            except RuntimeError as err:
                print('ERROR:', err)
                self.et.exitCalibration()

    class window:
        """EyeLink Display PC window object manager.

        :ivar parent: The eyeLink class object that the window is managed by.
        :vartype parent: eyeLink object
        :ivar fullscreen: Whether the window should be full screen.
        :vartype fullscreen: bool
        :ivar screensize: If not full screen, determines the screen size.
        :vartype screensize: tuple
        :ivar et: The EyeLink tracker object from the eyeLink parent object.
        :vartype et: EyeLink object
        :ivar dis: The pygame display surface
        :vartype dis: Surface
        :ivar surf: Possibly the same as dis # TODO check to see if this is the same
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
            
            self.dis = None
            if self.fullscreen:
                self.dis = pygame.display.set_mode((0, 0), FULLSCREEN | DOUBLEBUF)
                self.screensize = self.width, self.height = self.dis.get_size()
            else:
                # if fullscreen: self.dis = pygame.display.set_mode((0, 0), FULLSCREEN | DOUBLEBUF)
                self.dis = pygame.display.set_mode(self.screensize, 0)
                self.screensize = self.width, self.height = self.dis.get_size()

            pygame.display.set_caption('EVE')

            self.surf = pygame.display.get_surface()

        def show_message(self, message:str, fg_color:tuple[int, int, int], bg_color:tuple[int, int, int]) -> None:
            """Show messages on the display PC screen

            :param message: The message you would like to show
            :type message: str
            :param fg_color: RGB text colour
            :type fg_color: tuple[int, int, int]
            :param bg_color: RGB background colour
            :type bg_color: tuple[int, int, int]
            """

            # clear the screen and blit the texts
            self.surf.fill(bg_color)

            message_fnt = pygame.font.SysFont('Arial', 32)
            msgs = message.split('\n')
            for i in range(len(msgs)):
                message_surf = message_fnt.render(msgs[i], True, fg_color)
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
            parent = self.parent

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

                    if (ev.type == KEYDOWN) and (ev.key == K_c):
                        if ev.mod in [KMOD_LCTRL, KMOD_RCTRL, 4160, 4224]:
                            parent.terminate_task()

            # clear the screen following each keyboard response
            win_surf = pygame.display.get_surface()
            win_surf.fill(parent.genv.getBackgroundColor())
            pygame.display.flip()

            return resp

        def abort(self) -> pylink.TRIAL_ERROR:
            """Ends recording. 100 msec are added to catch final events.

            :return: Trial Error
            :rtype: pylink.TRIAL_ERROR
            """

            # get the currently active tracker object (connection)
            et = pylink.getEYELINK()
            if et != self.et: print("trackers not the same?")

            # Stop recording
            if self.et.isRecording():
                # add 100 ms to catch final trial events
                pylink.pumpDelay(100)
                self.et.stopRecording()

            # clear the screen
            surf = pygame.display.get_surface()
            surf.fill((128, 128, 128))
            pygame.display.flip()
            # Send a message to clear the Data Viewer screen
            self.et.sendMessage('!V CLEAR 128 128 128')

            # send a message to mark trial end
            self.et.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_ERROR)

            return pylink.TRIAL_ERROR

    def driftCheck(self, dc_x:int, dc_y:int, bgColour:tuple[int, int, int]=GREY, circleColour:tuple[int, int, int]=RED, circleRad:int=10) -> pylink.ABORT_EXPT:
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
        while not self.dm:
            surf = self.win.surf

            # terminate the task if no longer connected to the tracker or
            # user pressed Ctrl-C to terminate the task
            if (not self.et.isConnected()) or self.et.breakPressed():
                self.terminate()
                return pylink.ABORT_EXPT

            # draw a custom drift-correction target;
            # note that here the "draw_target" parameter is set to 0, i.e.,
            # user draw the target instead
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
    
    def terminate(self) -> None:
        """Terminate the task safely and retrieve the EDF data file.
        """

        # disconnect from the tracker if there is an active connection
        et = pylink.getEYELINK()
        if et != self.et: print("trackers not the same?")

        if self.et.isConnected():
            # Terminate the current trial first if the task terminated prematurely
            error = self.et.isRecording()
            if error == pylink.TRIAL_OK:
                self.win.abort()

            # Put tracker in Offline mode
            self.et.setOfflineMode()

            # Clear the Host PC screen and wait for 500 ms
            self.et.sendCommand('clear_screen 0')
            pylink.msecDelay(500)

            # Close the edf data file on the Host
            self.et.closeDataFile()

            # Show a file transfer message on the screen
            msg = 'EDF data is transferring from EyeLink Host PC...'
            self.win.show_message(msg, (0, 0, 0), (128, 128, 128))

            # Download the EDF data file from the Host PC to a local data folder
            # parameters: source_file_on_the_host, destination_file_on_local_drive
            local_edf = os.path.join(self.folders["s"], self.id + '.EDF')
            try:
                self.et.receiveDataFile(self.folders["f"], local_edf)
            except RuntimeError as error:
                print('ERROR:', error)

            # Close the link to the tracker.
            self.et.close()

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
        # put the tracker in the offline mode first
        self.et.setOfflineMode()

        # send a "TRIALID" message to mark the start of a trial, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        self.et.sendMessage('TRIALID %d' % trial_index)

        # record_status_message : show some info on the Host PC
        # here we show how many trial has been tested
        status_msg = 'TRIAL number %d, %s' % (trial_index, condition)
        self.et.sendCommand("record_status_message '%s'" % status_msg)

    def record(self) -> pylink.TRIAL_ERROR:
        """Begin the EyeTracker recording

        :return: Nothing or pylink.TRIAL_ERROR if runtime error
        :rtype: None or pylink.TRIAL_ERROR
        """
        # put tracker in idle/offline mode before recording
        self.et.setOfflineMode()

        # Start recording
        # arguments: sample_to_file, events_to_file, sample_over_link,
        # event_over_link (1-yes, 0-no)
        try:
            self.et.startRecording(1, 1, 1, 1)
        except RuntimeError as error:
            print("ERROR:", error)
            self.win.abort()
            return pylink.TRIAL_ERROR

        # Allocate some time for the tracker to cache some samples
        pylink.pumpDelay(100)

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
            ias = 'IA_%d.ias' % trial_index
            ias_path = os.path.join(self.folders["aoi"], ias)
            self.folders["ias"] = ias_path
            self.et.sendMessage('!V IAREA FILE %s' % ias_path)
            self.ias_file = open(self.folders["ias"], 'w')
        self.ias_file.write(msg)

    def stopRecording(self, trial_info:list, trial_labels:list=None) -> None:
        """Stops recording, and uploads trial info to EDF file.

        :param trial_info: Trial info for EDF file.
        :type trial_info: list
        :param trial_labels: List of data for the trials, defaults to None
        :type trial_labels: list, optional
        """
        # close the IAS file that contains the dynamic IA definition
        self.ias_file.close()

        # stop recording; add 100 msec to catch final events before stopping
        pylink.pumpDelay(100)
        self.et.stopRecording()

        # record trial variables to the EDF data file, for details, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        for message in trial_info:
            self.et.sendMessage(message)
            pylink.msecDelay(4)

        if trial_labels:
            self.et.sendMessage(f"!V TRIAL_VAR_DATA {trial_labels}")

        
        # send a 'TRIAL_RESULT' message to mark the end of trial, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        self.et.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_OK)
        
    def drawHostLine(self, pos1:tuple[int, int], pos2:tuple[int, int], colour:int) -> None:
        """Draws a line on the Host PC between two positions

        :param pos1: Position 1 (x, y)
        :type pos1: tuple[int, int]
        :param pos2: Position 2 (x, y)
        :type pos2: tuple[int, int]
        :param colour: The line colour
        :type colour: int

        The color codes supported on the Host PC range between 0-15
        0 - black, 1 - blue, 2 - green, 3 - cyan, 4 - red, 5 - magenta,
        6 - brown, 7 - light gray, 8 - dark gray, 9 - light blue,
        10 - light green, 11 - light cyan, 12 - light red,
        13 - bright magenta,  14 - yellow, 15 - bright white;\\
        see /elcl/exe/COMMANDs.INI on the Host
        """
        self.et.sendCommand('draw_line %d %d %d %d %d' % (pos1, pos2, colour))

    def clearHostScreen(self, colour:int=0) -> None:
        """Clears the Host PC's screen

        :param colour: If you want a different colour from black, input colour code, defaults to 0
        :type colour: int, optional

        The color codes supported on the Host PC range between 0-15
        0 - black, 1 - blue, 2 - green, 3 - cyan, 4 - red, 5 - magenta,
        6 - brown, 7 - light gray, 8 - dark gray, 9 - light blue,
        10 - light green, 11 - light cyan, 12 - light red,
        13 - bright magenta,  14 - yellow, 15 - bright white;\\
        see /elcl/exe/COMMANDs.INI on the Host
        """
        self.et.sendCommand(f'clear_screen {colour}')
                            
    def clearDVScreen(self, colour:tuple[int,int,int]=GREY) -> None:
        """Tells DataViewer to clear the screen.

        :param colour: RGB cleared screen colour, defaults to GREY
        :type colour: tuple[int,int,int], optional
        """
        # send a message to clear the Data Viewer screen as well
        self.et.sendMessage('blank_screen')
        self.et.sendMessage('!V CLEAR %d %d %d' % (colour))

    def checkDisconnect(self) -> bool:
        """Checks if the EyeLink has diconnected.

        :return: If the EyeLink is disconnected.
        :rtype: bool
        """
        error = self.et.isRecording()
        if error is not pylink.TRIAL_OK:
            self.et.sendMessage('tracker_disconnected')
            self.win.abort()
            self.error = error
            return True
        else: return False













