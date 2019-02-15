import time
import RPi.GPIO as GPIO


class SharedResources:

    def __init__(self):
        pin = 7
        freq = 50  # 50 Hz
        pos = 4  # initial duty cycle, position maximum open
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT)
        self.p = GPIO.PWM(pin, freq)
        self.p.start(pos)  # initiate as open
        time.sleep(0.5)

    def open_gripper(self):
        print("start open")
        dc_open = 4  # duty cycle for gripper totally open
        self.p.ChangeDutyCycle(dc_open)
        time.sleep(1)

    def close_gripper(self):
        print("start close")
        dc_close = 6  # duty cycle for gripper totally closed
        self.p.ChangeDutyCycle(dc_close)
        time.sleep(1)

    def close_totally(self):
        dc_close = 9  # duty cycle for gripper totally closed
        self.p.ChangeDutyCycle(dc_close)
        time.sleep(1)

    def reset_gripper(self):
        print('reset gripper')
        self.p.stop()


class GRIPPER:
    resources = SharedResources()

    def schedule(self, event_name, event_value, OPE):
        if event_name == 'REQ':
            if OPE == 1:
                self.resources.open_gripper()
            elif OPE == 2:
                self.resources.close_gripper()
            elif OPE == 3:
                self.resources.close_totally()
            elif OPE == 4:
                self.resources.reset_gripper()

            return [event_value]
