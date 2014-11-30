wakeupPro
=========
Alarm clock in Python by void-.

Given a time, calculate the difference between now and that time. Wait until
that time, then activate an alarm. To deactivate the alarm, the user must
correctly enter the random string that is printed to the screen. New settings
file, once you set the sound clip you want, you no longer need to use -s in the
when running the program next time.

Additional features:
* Option for an acclamitory beep (-a)
    - The alarm will make an exponential regression of beeps at varying
    - frequencies to make waking up a more gradual process.
* Option for accelerated sleep (-x)
    - The alarm will beep a number of times 1 hour before the user is to wake
    - up but not require it to be shut off. This can lead to accelerated REM
    - sleep.
* Anti copy-paste mechanism
    - The output random string cannot be directly copied and pasted to shut off
      the alarm.
* Logging
    - Logs how long the alarm sleeps on a certain day.
    - It also logs how long it takes for the alarm to be shut off for a metric
      of fatigue.
* Option to change alarm tone (-s)
    - Either give the path to your own alarm tone or use one of the three built 
      in ones [0-2]

Command Line Usage:
Notes: Must use Python 2.x; arguments can be in any order
python wakeup_pro.py [-ax] [-s file] [HH:MM]
