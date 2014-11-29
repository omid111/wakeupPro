from sys import argv
from os import system
from time import sleep, strptime
from random import randint, choice
import threading, datetime

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
    DICT_PATH path for the dictionary used for the deactivation code.

  Member Variables:
    wakeupTime datetime object for when the alarm is set to go off.
    acclimate boolean indicating if the alarm should make acclamitory beeps.
    _beeper Beeper instance for beeping on a separate thread.
    _dict python array with words from DICT_PATH.

  """

  SLEEP_MSG = ("Sweet Dreams","Goodnight")
  INCORRECT_MSG = "incorrect input"
  SHUTOFF_MSG = "Enter the following to terminate alarm:"
  ANTI_COPY_MSG = " "
  ACCLIMATE_LENGTH = 5 * 60
  ACCELERATE_BEEPS = 10
  ACCELERATE_TIME = 1 * 60 * 60
  BEEP_INTERVAL = 1
  CODE_LENGTH = (4,8)
  LOG_PATH = "./.sleeplog"
  DICT_PATH = "/etc/dictionaries-common/words"

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
    system("paplay /usr/share/sounds/ubuntu/stereo/message.ogg");
    #system("beep %s -e /dev/input/by-path/platform-pcspkr-event-spkr" % \
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

    with file(self.DICT_PATH, "r") as f:
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

    print self.SHUTOFF_MSG
    while raw_input("%s  %s\n  "%(stopCode, self.ANTI_COPY_MSG)) != stopCode:
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
    acclimate = ("-a" in argv)
    accelerate = ("-x" in argv)

    #Create a timestruct from user input if no argument was given
    timestruct = strptime((raw_input("Enter wakeup time in the format:" \
      " HH:MM ") if len(argv) < 2 else argv[1]),"%H:%M")

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
