# -*- coding: utf-8 -*-
"""
Created on Sat Jun 19 15:17:35 2021

@author: Guido di Pasquo
"""
from src import python_sitl_functions as Sim
import numpy as np
import importlib
class SITLProgram:
    def __init__(self):
        pass

    """ Available funtions, called with Sim.
    Sim.millis(), Sim.micros(),
    gyro, accx, accz, alt, pos_gnss, vel_gnss = Sim.getSimData()
    Sim.sendCommand(servo, parachute)
    Sim.plot_variable(variable, number) (from 1 to 5 for diferent plots)
    -->
    -->
    -->
    -->
    -->
    -->
    -->
    -->
    -->
    -->
    """
    """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""

    def everything_that_is_outside_functions(self):
        module = "pid_module"
        self.pid_module = importlib.import_module("SITL Modules.Complemetary Modules."
                                                      +module)

        self.DEG2RAD = np.pi / 180
        self.RAD2DEG = 1 / self.DEG2RAD
        self.fin_max = 30 / 57.3
        self.pid_pitch = self.pid_module.PID(3, 0.5, 0.3, True, self.fin_max)
        self.pid_pos = self.pid_module.PID(1/20, 0.01, 0.005, False, 5)
        self.k_all = -5
        self.actuator_reduction = 1

        self.u_controller = 0
        self.u_prev = 0
        self.u_servos = 0
        self.t_prev = -0.001
        self.last_error = 0
        self.cum_error = 0
        self.theta = 0
        self.timer_all = 0
        self.sample_time_program = 0.005
        self.i = 0
        self.vel_glob = [0,0]
        self.pos_glob_acc = [0,0]
        self.alt_prev = 0
        self.pos_corrected = [0,0]
        self.pos_gnss_prev = 0







    def void_setup(self):
        pass







    def void_loop(self):
        self.t = Sim.micros()/1000000
        if self.t >= self.timer_all + self.sample_time_program*0.999:
            self.timer_all = self.t
            self.delta_t = self.t - self.t_prev
            self.t_prev = self.t
            self.gyro, self.accx, self.accz, self.alt, self.pos_gnss, self.vel_gnss = Sim.getSimData()
            self.convert_measurement_system()
            self.integrate_gyro()
            self.integrate_accelerometer()
            self.compute_position_acc_and_gnss()
            inp_pos = 0-self.pos_corrected[1]
            setpoint = self.pid_pos.compute_output(-inp_pos, self.t)
            inp_pitch = self.theta
            servo = self.control(setpoint, inp_pitch, self.t) * self.RAD2DEG
            parachute = self.parachute_deployment()
            Sim.sendCommand(servo, parachute)
            Sim.plot_variable(self.pos_corrected[1], 1)
            Sim.plot_variable(self.theta*self.RAD2DEG, 2)






    """########"""

    def control(self, setpoint, inp, t):
        self.u_prev = self.u_controller
        error = setpoint - inp
        error = error * self.k_all
        self.u_controller = self.pid_pitch.compute_output(error, t)
        # Saturation
        if self.u_controller > self.fin_max:
            self.u_controller = self.fin_max
        elif self.u_controller < -self.fin_max:
            self.u_controller = -self.fin_max
        # u_controller=u_controller-u_prev*0.05;  #filter, increasing the
        # number makes it stronger and slower
        self.u_servos = self.u_controller * self.actuator_reduction
        return self.u_servos

    def parachute_deployment(self):
        if self.alt < self.alt_prev and self.alt > 10:
            return 1
        else:
            self.alt_prev = self.alt
            return 0

    def integrate_gyro(self):
        self.theta += self.gyro * self.delta_t

    def integrate_accelerometer(self):
        self.acc_glob_measured = self.loc2glob(self.accx, self.accz, self.theta)
        self.acc_glob = [self.acc_glob_measured[0]-9.8, self.acc_glob_measured[1]]
        self.pos_glob_acc[0] += self.vel_glob[0] * self.delta_t
        self.pos_glob_acc[1] += self.vel_glob[1] * self.delta_t
        self.vel_glob[0] += self.acc_glob[0] * self.delta_t
        self.vel_glob[1] += self.acc_glob[1] * self.delta_t

    def loc2glob(self, u0,v0,theta):
        A = np.array([[np.cos(theta), np.sin(theta)],
                    [-np.sin(theta), np.cos(theta)]])
        u = np.array([[u0],[v0]])
        x = np.dot(A,u)
        a = [x[0,0],x[1,0]]
        return a

    def glob2loc(u0,v0,theta):
        A = np.array([[np.cos(theta), -np.sin(theta)],
                    [np.sin(theta), np.cos(theta)]])
        u = np.array([[u0],[v0]])
        x = np.dot(A,u)
        a = [x[0,0],x[1,0]]
        return a

    def compute_position_acc_and_gnss(self):
        if self.pos_gnss != self.pos_gnss_prev:
            self.vel_glob[1] = self.vel_gnss
            self.pos_glob_acc[1] = self.pos_gnss
            self.pos_gnss_prev = self.pos_gnss
        self.pos_corrected[0] = self.alt
        self.pos_corrected[1] = self.pos_glob_acc[1]

    def convert_measurement_system(self):
        self.gyro *= self.DEG2RAD
        self.accx *= 9.8
        self.accz *= 9.8
