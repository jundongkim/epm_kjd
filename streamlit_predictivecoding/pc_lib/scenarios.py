import numpy as np

# =======================
# Scenario Generators
# =======================
def gen_sine(t, amp, freq, noise):
    return amp * np.sin(2 * np.pi * freq * t) + np.random.normal(0, noise, size=np.array(t).shape)

def gen_step(t, amp, step_time, noise):
    return (amp if t > step_time else 0) + np.random.normal(0, noise)

def gen_random_walk(prev, noise):
    return prev + np.random.normal(0, noise) 