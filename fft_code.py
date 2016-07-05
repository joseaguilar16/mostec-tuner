from numpy import fft
import numpy as np
import matplotlib.pyplot as plt
import time
import spidev
import wave
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

GPIO.setup(5,GPIO.IN)

GPIO.setup(17,GPIO.OUT)
GPIO.setup(27,GPIO.OUT)
GPIO.setup(4,GPIO.OUT)

outs = [17,27,4]
for x in outs:
    GPIO.output(x,0)   

spi = spidev.SpiDev()
spi.open(0,0)

def readChannel(channel):
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data



#this function takes in a string of data and the sampling period of the data (how far apart in time each sample was taken...for you it will probably be 1/4000 seconds.

#It then performs an FFT and returns location of the major frequency components.
#If you uncomment the plt.plot and plt.show() lines below this will

def frequency_extractor(data,time):
    n = len(data)
    Fk = fft.fft(data)/n
    nu = fft.fftfreq(n,time)
    Fk = fft.fftshift(Fk)
    nu = fft.fftshift(nu)
    power = np.absolute(Fk)**2
    #plt.plot(nu,power)
    #plt.show()
    mid_point = len(nu)
    new_power = power[int(mid_point/2)+2:]
    new_nu = nu[int(mid_point/2)+2:]
    #print new_power
    #print new_nu
    maxi = np.argmax(new_power)
    #print new_nu[maxi]
    #print max(power)
    return new_nu[maxi]

# The code below will try to as quickly as possible, take data points (10,000 of them)...it will then equally space them out at about 1/4000 seconds (to safely account for jitter)...and then

num_samples = 10000
start = time.time()
sample_rate = 4000
delay = 1.0/sample_rate

#make pre-sized array to not waste time during writes relating to resizing arrays:
#first array for measurements.
#second array for timestamps:
data = [0 for x in xrange(num_samples)]
tim = [0 for x in xrange(num_samples)]
#take data:
for x in xrange(num_samples):
    data[x]=(readChannel(1))
    tim[x] = time.time() 

#correct for time:
timm = [x - tim[0] for x in tim]
timm = timm + range(15,50) #buffer
total = time.time()-start

#determine approximate average sample rate:
actual_sample_rate = 1.0*num_samples/total
sample_duration = 1.0/actual_sample_rate

down_sampled = []
sample_number = 0

sample_number = 0
fourk = []
data = data + data[-50:] #add on buffer at end for iteration protection
for x in range(int(total*4000)):
    while x*1.0/4000.0 >= timm[sample_number]:
        sample_number +=1
    fourk.append(data[sample_number]) 

#fourk contains the data sampled at 4000 Hz:
#print frequency_extractor(fourk,1.0/sample_rate)

note = [['A4',440.0],['B4',493.88],['C5',523.25],['D5',587.33],['E5',659.25]]

try:
    while True: 
        if GPIO.input(5) == 0:
            for x in outs:
                GPIO.output(x,0)
            nn = ' '
            pitch = False
            out = False
            GPIO.output(4,1)
            time.sleep(1)
            #
            #how to reset
            #
            freq = frequency_extractor(fourk,1.0/sample_rate)
            print freq
            GPIO.output(4,0)
            for y in [0,1,2,3,4]:
                if freq >= (note[y][1] - 1.0) and freq <= (note[y][1] + 1.0):
                    nn = note[y][0]
                    pitch = True
            if pitch == False:
                out = True
                nn = 'OUT of tune.'
            if pitch == True:
                GPIO.output(27,1)
                print 'The note is ' + nn +'\n'
            if out == True:
                GPIO.output(17,1)
                print 'The note is ' + nn +'\n'
except KeyboardInterrupt:
    for x in outs: #turn off all LEDs
        GPIO.output(x,0)
finally:
    for x in outs:
        GPIO.output(x,0)
    GPIO.cleanup()




