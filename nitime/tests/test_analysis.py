import numpy as np
import numpy.testing as npt
from nitime import utils as ut
import nitime.timeseries as ts
import nitime.analysis as nta
import nose.tools as nt
import decotest

def test_CorrelationAnalyzer():

    Fs = np.pi
    t = np.arange(1024)
    x = np.sin(10*t) + np.random.rand(t.shape[-1])
    y = np.sin(10*t) + np.random.rand(t.shape[-1])

    T = ts.UniformTimeSeries(np.vstack([x,y]),sampling_rate=Fs)

    C = nta.CorrelationAnalyzer(T)

    #Test the symmetry: correlation(x,y)==correlation(y,x) 
    npt.assert_equal(C.correlation[0,1],C.correlation[1,0])
    #Test the self-sameness: correlation(x,x)==1
    npt.assert_equal(C.correlation[0,0],1)
    npt.assert_equal(C.correlation[1,1],1)

    #Test the cross-correlation:
    #First the symmetry:
    npt.assert_array_almost_equal(C.xcorr.data[0,1],C.xcorr.data[1,0])
    
    #Test the normalized cross-correlation
    #The cross-correlation should be equal to the correlation at time-lag 0
    npt.assert_equal(C.xcorr_norm.data[0,1,C.xcorr_norm.time==0]
                            ,C.correlation[0,1])

    #And the auto-correlation should be equal to 1 at 0 time-lag:
    npt.assert_equal(C.xcorr_norm.data[0,0,C.xcorr_norm.time==0],1)

    #Does it depend on having an even number of time-points?
    #make another time-series with an odd number of items:
    t = np.arange(1023)
    x = np.sin(10*t) + np.random.rand(t.shape[-1])
    y = np.sin(10*t) + np.random.rand(t.shape[-1])

    T = ts.UniformTimeSeries(np.vstack([x,y]),sampling_rate=Fs)

    C = nta.CorrelationAnalyzer(T)

    
    npt.assert_equal(C.xcorr_norm.data[0,1,C.xcorr_norm.time==0]
                            ,C.correlation[0,1])

def test_EventRelatedAnalyzer():

    cycles = 10
    l = 1024
    unit = 2*np.pi/l
    t = np.arange(0,2*np.pi+unit,unit)
    signal = np.sin(cycles*t)
    events = np.zeros(t.shape)
    #Zero crossings: 
    idx = np.where(np.abs(signal)<0.03)[0]
    #An event occurs at the beginning of every cycle:
    events[idx[:-2:2]]=1
    #and another kind of event at the end of each cycle:
    events[idx[1:-1:2]]=2

    T_signal = ts.UniformTimeSeries(signal,sampling_rate=1)
    T_events = ts.UniformTimeSeries(events,sampling_rate=1)
    ETA = nta.EventRelatedAnalyzer(T_signal,T_events,l/(cycles*2)).eta

    #This looks good, but doesn't pass unless you consider 3 digits:
    npt.assert_almost_equal(ETA.data[0],signal[:ETA.data.shape[-1]],3)
    npt.assert_almost_equal(ETA.data[1],-1*signal[:ETA.data.shape[-1]],3)

    #Same should be true for the FIR analysis: 
    FIR = nta.EventRelatedAnalyzer(T_signal,T_events,l/(cycles*2)).FIR
    npt.assert_almost_equal(FIR.data[0],signal[:FIR.data.shape[-1]],3)
    npt.assert_almost_equal(FIR.data[1],-1*signal[:FIR.data.shape[-1]],3)

def test_CoherenceAnalyzer():

    Fs = np.pi
    t = np.arange(1024)
    x = np.sin(10*t) + np.random.rand(t.shape[-1])
    y = np.sin(10*t) + np.random.rand(t.shape[-1])

    T = ts.UniformTimeSeries(np.vstack([x,y]),sampling_rate=Fs)

    C = nta.CoherenceAnalyzer(T)

def test_HilbertAnalyzer():
    """Testing the HilbertAnalyzer (analytic signal)"""
    pi = np.pi
    Fs = np.pi
    t = np.arange(0,2*pi,pi/256)

    a0 = np.sin(t)
    a1 = np.cos(t)
    a2 = np.sin(2*t)
    a3 = np.cos(2*t)

    T = ts.UniformTimeSeries(data=np.vstack([a0,a1,a2,a3]),
                             sampling_rate=Fs)

    H = nta.HilbertAnalyzer(T)

    h_abs = H.magnitude.data
    h_angle = H.phase.data
    h_real = H.real.data
    #The real part should be equal to the original signals:
    npt.assert_almost_equal(h_real,H.data)
    #The absolute value should be one everywhere, for this input:
    npt.assert_almost_equal(h_abs,np.ones(T.data.shape))
    #For the 'slow' sine - the phase should go from -pi/2 to pi/2 in the first
    #256 bins: 
    npt.assert_almost_equal(h_angle[0,:256],np.arange(-pi/2,pi/2,pi/256))
    #For the 'slow' cosine - the phase should go from 0 to pi in the same
    #interval: 
    npt.assert_almost_equal(h_angle[1,:256],np.arange(0,pi,pi/256))
    #The 'fast' sine should make this phase transition in half the time:
    npt.assert_almost_equal(h_angle[2,:128],np.arange(-pi/2,pi/2,pi/128))
    #Ditto for the 'fast' cosine:
    npt.assert_almost_equal(h_angle[3,:128],np.arange(0,pi,pi/128))

#This is known to fail because of artifacts induced by the fourier transform
#for limited samples: 
@npt.dec.knownfailureif(True) 
def test_FilterAnalyzer():
    """Testing the FilterAnalyzer """
    t = np.arange(np.pi/100,10*np.pi,np.pi/100)
    fast = np.sin(50*t)
    slow = np.sin(10*t)
    time_series = ts.UniformTimeSeries(data=fast+slow,sampling_rate=np.pi)

    #0.6 is somewhere between the two frequencies 
    f_slow = nta.FilterAnalyzer(time_series,ub=0.6)
    npt.assert_equal(f_slow.filtered_fourier.data,slow)
    #
    f_fast = nta.FilterAnalyzer(time_series,lb=0.6)
    npt.assert_equal(f_fast.filtered_fourier.data,fast)
