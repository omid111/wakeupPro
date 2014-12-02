from sys import argv
from time import sleep, strptime
from random import randint, choice
import threading, datetime
import urllib
import os

#Global Variables
#SETTINGS_PATH path for the .alarmsettings file
SETTINGS_PATH = "./.alarmsettings"
#DICT_PATH path for the dictionary used for the deactivation code.
DICT_PATH = ""
#SOUND_PATH path for the alarm alert sound clip
SOUND_PATH = ""

def initialize(dp="", sp=0, sfile=""):
  """Initialization method, reads path values for:
  - DICT_PATH
  from .alarmsettings file. If the file doesn't exist, then create a new 
  .alarmsettings file.
  """
  global DICT_PATH, SOUND_PATH
  sounds = ["message.ogg","drip.ogg","glass.ogg"]

  try:
    settingsfile = open(SETTINGS_PATH, "r")
    for line in settingsfile:
      if("DICT_PATH" == line[0:9]):
        DICT_PATH = line[11:-1]
      elif("SOUND_PATH" == line[0:10]):
        SOUND_PATH = line [12:-1]
    if DICT_PATH == "" or SOUND_PATH == "":
      os.remove(SETTINGS_PATH)
      print("Error. Please run program again.")
      exit(1)
  except IOError:
    settingsfile = open(SETTINGS_PATH, "wb")
    for dictn in [dp,"/etc/dictionaries-common/words",\
                  "/usr/share/dict/words","words"]:
      if(os.path.isfile(dictn)):
        DICT_PATH = dictn
        settingsfile.write("DICT_PATH: " + DICT_PATH + "\n")
        break;
    for sound in [sfile, sounds[sp], \
                  "/usr/share/sounds/ubuntu/stereo/message.ogg"] + sounds:
      if(os.path.isfile(sound)):
        SOUND_PATH = sound
        settingsfile.write("SOUND_PATH: " + SOUND_PATH + "\n")
        break;
    if DICT_PATH == "":
      print "You don't have /usr/share/dict/words file, downloading and"+ \
              "placing in current directory"
      wf = urllib.URLopener()
      wf.retrieve("http://www.cs.duke.edu/~ola/ap/linuxwords", "words")
      DICT_PATH = "./words"
      settingsfile.write("DICT_PATH: " + DICT_PATH + "\n")

  settingsfile.close()

class Alarm(object):
  """Alarm object that, given a time to wakeup, can sleep and then beep.

  Shutting off the alarm requires the user to input a generated sequence
  of dictionary words. Relevant data is logged throughout the process.

  Class Variables:
    SLEEP_MSG tuple containing possible messages to display once activated.
    INCORRECT_MSG string to display when shutoff input does not match.
    SHUTOFF_MSG string to display when user is prompted to shutoff alarm.
    ANTI_COPY_MSG string that is invisible and affects terminal copying.
    ACCLIMATE_LENGTH the length of acclimation time in seconds.
    BEEP_INTERVAL number of seconds between alarm beeps beeps.
    CODE_LENGTH tuple defining a lower and upper bounds for the code length.
    LOG_PATH path for the log file.

  Member Variables:
    wakeupTime datetime object for when the alarm is set to go off.
    acclimate boolean indicating if the alarm should make acclamitory beeps.
    _beeper Beeper instance for beeping on a separate thread.
    _dict python array with words from DICT_PATH.

  """

  SLEEP_MSG = ("Sweet Dreams","Goodnight","Night","gn")
  INCORRECT_MSG = "incorrect input"
  SHUTOFF_MSG = "Enter the following to terminate alarm:"
  ANTI_COPY_MSG = "_"
  ACCLIMATE_LENGTH = 5 * 60
  ACCELERATE_BEEPS = 10
  ACCELERATE_TIME = 1 * 60 * 60
  BEEP_INTERVAL = 1
  CODE_LENGTH = (4,8)
  LOG_PATH = "./.sleeplog"

  def __init__(self, wakeupTime, acclimate=False, accelerate=False):
    """Initialize an Alarm given wakeup time and optional acclimate boolean."""

    self.wakeupTime = wakeupTime
    self.acclimate = acclimate
    self.accelerate = accelerate
    self._beeper = Beeper()
    self._dict = {}

  @staticmethod
  def BEEP(frequency=-1):
    """Make the computer beep by the internal speaker with optional frequency.

    If no frequency is specified, the system default is used.
    The current implementation relies on system calls to beep.
    This method may need to be adjusted depending upon the system.

    """
    os.system("paplay "+SOUND_PATH);
    #os.system("paplay /usr/share/sounds/ubuntu/stereo/message.ogg");
    #os.system("beep %s -e /dev/input/by-path/platform-pcspkr-event-spkr" % \
    #  ("" if (frequency == -1) else ("-f %i" %frequency)))

  @staticmethod
  def SLEEP(seconds):
    """Sleep for a given number of seconds without using cpu."""

    sleep(seconds)

  @staticmethod
  def ACCLIMATE_PATTERN(iteration):
    """Return a number in an exponential regression for a given iteration."""

    return .5274 * (iteration**(-1.5214))

  def startBeeps(self):
    """Start a beep thread and beep until stop is called."""

    self._beeper.start()

  def stopBeeps(self):
    """Stop the beep thread."""

    self._beeper.stop()

  def loadDict(self):
    """Load all entries from DICT_PATH into _dict and remove newlines."""

    with file(DICT_PATH, "r") as f:
      i = 0
      for line in f.readlines():
        self._dict[i] = line.rstrip("\n")
        i+=1

  def startAlarm(self):
    """Start the alarm clock and sleep and start beeping when done.

    The procedure:
    Display a random sleep message to the user. Compute the number of
    seconds between the time the alarm is started and the time to wakeup.
    Log when the user goes to sleep and wait. If acclamitory beeps are
    enabled, wait for less time and then make occasional beeps, waiting
    in-between. When its time for the user to wake-up, start a beeping
    thread.

    """

    #Print sleep message
    print(choice(self.SLEEP_MSG))
    now = datetime.datetime.today()
    wait = (self.wakeupTime - now).total_seconds()
    self.logSleep(now, wait)
    if(self.accelerate and wait > self.ACCELERATE_TIME):
      Alarm.SLEEP(wait - self.ACCELERATE_TIME)
      wait -= (wait - self.ACCELERATE_TIME) #setup for acclimate
      for _ in xrange(self.ACCELERATE_BEEPS):
        Alarm.BEEP()
    if (self.acclimate and wait > self.ACCLIMATE_LENGTH):
      Alarm.SLEEP(wait - self.ACCLIMATE_LENGTH)
      for i in xrange(1,6):
        i = self.ACCLIMATE_PATTERN(i)#Reassign i so its value can be used
        Alarm.BEEP(4000*i)#Modulate the frequency
        Alarm.SLEEP(self.ACCLIMATE_LENGTH * i)
    else:
      self.SLEEP(wait)
    #Start beeping
    self.startBeeps()

  def stopAlarm(self):
    """Stop the alarm clock when the user enters the correct word sequence."""

    start = datetime.datetime.today()
    self.loadDict() #Load the dictionary
    #Construct a phrase from a random number of random words in the dictionary
    stopCode = " ".join(self._dict[randint(0, len(self._dict))-1] \
      for _ in xrange(randint(*self.CODE_LENGTH)))

    printCode = self.ANTI_COPY_MSG.join(stopCode.split(" "))

    print self.SHUTOFF_MSG
    while raw_input("%s  %s\n  "%(printCode, self.ANTI_COPY_MSG)) != stopCode:
      print(self.INCORRECT_MSG)
    self.stopBeeps()
    stop = datetime.datetime.today()

    #Mark dictionary for garbage collection
    self._dict = None
    self.logStop((stop - start).total_seconds())

  def logSleep(self, date, sleepTime):
    """Write to the log on which date for how long the alarm slept.

    Given a datetime object and the number of seconds slept, write
    to the log in the following format:
      YYYY-MM-DD HH:MM:SS.SSSSSS, #ofSeconds\n
    Ex.:
      2013-07-06 13:21:12.632746, 10856

    """
    with file(self.LOG_PATH,"a") as f:
      f.write("%s, %s\n" % (str(date), str(sleepTime)))

  def logStop(self, time):
    """Write to the log how long it look for the alarm to stop.

    Given a floating point number representing the number of seconds it took
    for the alarm to stop, write it to the log in the following format:
      stop: #\n

    """

    with file(self.LOG_PATH,"a") as f:
      f.write("stop: %s\n" % str(time))

  @staticmethod
  def main(argv):
    """Main method.

    If no time is given as an argument, accept input from the user.
    Create an alarm and start it to go off for the specified time.
    If given as an argument, create the alarm to make acclamitory beeps.

    """
    #Go through arguments, make sure they are all valid
    acclimate = accelerate = False
    timeindex = -1
    if("-s" not in argv):
      initialize()
    for i in xrange(len(argv)):
      if argv[i][0] == '-':
        for op in argv[i][1:]:
          if op == 'a':
            acclimate = True
          elif op == 'x':
            accelerate = True
          elif op == 's':
            os.remove(".alarmsettings")
            i += 1
            try:
              initialize(sp=int(argv[i]))
            except ValueError:
              intialize(sfile=argv[i])
          else:
            print "Unknown option -" + op
      elif ':' in argv[i]:
        timeindex = i

    #Create a timestruct from user input if no argument was given
    timestruct = strptime((raw_input("Enter wakeup time in the format:" \
      " HH:MM ") if timeindex == -1 else argv[timeindex]),"%H:%M")

    today = datetime.datetime.today()
    time = datetime.datetime(today.year, today.month, today.day, \
      timestruct.tm_hour, minute = timestruct.tm_min)
    #If the time has happened already, assume its for tomorrow: add 1 day
    if today > time:
      time+=datetime.timedelta(1)

    a = Alarm(time, acclimate, accelerate)
    a.startAlarm()
    a.stopAlarm()

class Beeper(threading.Thread):
  """Beeper object that beeps on another thread until stopped.

  Subclasses Thread and overrides the run method to beep. The
  beeping thread is started by calling run() and stopped by
  a call to stop(). Once stop() is called, run() has no effect.

  Member Variables:
    _beep boolean indicating if the Beeper should beep.
      Call stop() to set this to False and terminate the thread.

  """

  def __init__(self):
    """Initialize a Beeper."""

    threading.Thread.__init__(self, None, None, None, (), {})
    self._beep = True

  def run(self):
    """Beep and wait a certain interval until stop() is called."""

    while self._beep:
      Alarm.BEEP()
      Alarm.SLEEP(Alarm.BEEP_INTERVAL)

  def stop(self):
    """Stop the beeping thread.

    If the Beeper is not currently beeping,
    calls to run() will have no effect.

    """
    self._beep = False

#Execute the main method
if __name__ == "__main__":
  Alarm.main(argv)
