import ctypes

# Load the shared object file
lib = ctypes.CDLL('./pylink_c.so')

# Define the argument and return types for each function
lib.EyeLinkCBind.argtypes = []
lib.EyeLinkCBind.restype = ctypes.c_void_p

lib.msecDelay.argtypes = [ctypes.c_int]
lib.msecDelay.restype = None

lib.openCustomGraphicsInternal.argtypes = []
lib.openCustomGraphicsInternal.restype = ctypes.c_void_p

lib.getDisplayInformation.argtypes = [ctypes.POINTER(ctypes.c_int)]
lib.getDisplayInformation.restype = ctypes.c_int

lib.inRealTimeMode.argtypes = [ctypes.c_int]
lib.inRealTimeMode.restype = ctypes.c_int

lib.flushGetkeyQueue.argtypes = []
lib.flushGetkeyQueue.restype = None

lib.beginRealTimeMode.argtypes = [ctypes.c_int]
lib.beginRealTimeMode.restype = ctypes.c_int

lib.currentTime.argtypes = []
lib.currentTime.restype = ctypes.c_int

lib.currentUsec.argtypes = []
lib.currentUsec.restype = ctypes.c_int

lib.endRealTimeMode.argtypes = []
lib.endRealTimeMode.restype = ctypes.c_int

lib.pumpDelay.argtypes = [ctypes.c_int]
lib.pumpDelay.restype = None

lib.alert.argtypes = [ctypes.c_char_p]
lib.alert.restype = None

lib.enableExtendedRealtime.argtypes = [ctypes.c_int]
lib.enableExtendedRealtime.restype = ctypes.c_int

lib.getLastError.argtypes = []
lib.getLastError.restype = ctypes.c_char_p

lib.enablePCRSample.argtypes = [ctypes.c_int]
lib.enablePCRSample.restype = ctypes.c_int

lib.enableUTF8EyeLinkMessages.argtypes = [ctypes.c_int]
lib.enableUTF8EyeLinkMessages.restype = ctypes.c_int

lib.bitmapSave.argtypes = [ctypes.c_char_p]
lib.bitmapSave.restype = ctypes.c_int

lib.sendMessageToFile.argtypes = [ctypes.c_char_p]
lib.sendMessageToFile.restype = ctypes.c_int

lib.openMessageFile.argtypes = [ctypes.c_char_p]
lib.openMessageFile.restype = ctypes.c_int

lib.closeMessageFile.argtypes = []
lib.closeMessageFile.restype = ctypes.c_int

lib.request_cross_hair_draw.argtypes = []
lib.request_cross_hair_draw.restype = ctypes.c_int

# Define wrapper functions
def eye_link_c_bind():
    """Wrapper for the EyeLinkCBind function."""
    return lib.EyeLinkCBind()

def msec_delay(milliseconds):
    """Wrapper for the msecDelay function."""
    lib.msecDelay(milliseconds)

def open_custom_graphics_internal():
    """Wrapper for the openCustomGraphicsInternal function."""
    return lib.openCustomGraphicsInternal()

def get_display_information(display_info):
    """Wrapper for the getDisplayInformation function."""
    return lib.getDisplayInformation(ctypes.byref(display_info))

def in_real_time_mode(param):
    """Wrapper for the inRealTimeMode function."""
    return lib.inRealTimeMode(param)

def flush_getkey_queue():
    """Wrapper for the flushGetkeyQueue function."""
    lib.flushGetkeyQueue()

def begin_real_time_mode(param):
    """Wrapper for the beginRealTimeMode function."""
    return lib.beginRealTimeMode(param)

def current_time():
    """Wrapper for the currentTime function."""
    return lib.currentTime()

def current_usec():
    """Wrapper for the currentUsec function."""
    return lib.currentUsec()

def end_real_time_mode():
    """Wrapper for the endRealTimeMode function."""
    return lib.endRealTimeMode()

def pump_delay(milliseconds):
    """Wrapper for the pumpDelay function."""
    lib.pumpDelay(milliseconds)

def alert(message):
    """Wrapper for the alert function."""
    lib.alert(message.encode('utf-8'))

def enable_extended_realtime(param):
    """Wrapper for the enableExtendedRealtime function."""
    return lib.enableExtendedRealtime(param)

def get_last_error():
    """Wrapper for the getLastError function."""
    return lib.getLastError().decode('utf-8')

def enable_pcr_sample(param):
    """Wrapper for the enablePCRSample function."""
    return lib.enablePCRSample(param)

def enable_utf8_eye_link_messages(enable):
    """Wrapper for enableUTF8EyeLinkMessages."""
    return lib.enableUTF8EyeLinkMessages(enable)

def open_custom_graphics_internal():
    """Wrapper for openCustomGraphicsInternal."""
    return lib.openCustomGraphicsInternal()

def bitmap_save(filename):
    """Wrapper for bitmapSave."""
    return lib.bitmapSave(filename.encode('utf-8'))

def send_message_to_file(message):
    """Wrapper for sendMessageToFile."""
    return lib.sendMessageToFile(message.encode('utf-8'))

def open_message_file(filename):
    """Wrapper for openMessageFile."""
    return lib.openMessageFile(filename.encode('utf-8'))

def close_message_file():
    """Wrapper for closeMessageFile."""
    return lib.closeMessageFile()

def request_cross_hair_draw(draw):
    """Wrapper for request_cross_hair_draw."""
    return lib.request_cross_hair_draw(draw)

