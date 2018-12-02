# -*- coding: utf-8 -*-
"""
    #tode: 1.refine the identification of prominence. 2.indicate the main saliency in the output figure produced by show_stylization()

"""
import matplotlib
import matplotlib.pylab as pl
import numpy as np
import SLAM_utils.TextGrid as tg
from SLAM_utils import praatUtil
from SLAM_utils import swipe
import os, math


def SLAM1(semitones):

    DOWNSAMPLE_ON = False

    #this takes a sequence of semitones and applies the SLAM1 stylization

    #first, smooth the semitones curves using LOWESS
    if 100<len(semitones) and DOWNSAMPLE_ON: 
        # ? why do a downsampling ?
        # 1.assumed that the signal is of narraowband due to the
        # the filtering processing by SWIPE
        # 2.make acceleration
        r = int(len(semitones)/100.0)
        semitones = list(np.array(semitones)[::r])

    t = np.array(range(len(semitones)))/float(len(semitones))
    if 10<len(semitones):
        import SLAM_utils.lowess as lowess
        smooth = lowess.lowess(t,semitones)
    else:
        smooth = semitones

    # identify the three essential points
    ti,fr=identifyThreeEssentialPoints(smooth)
    
    # transcript the model in SLAM annotation
    style = relst2register(fr[0])
    style+= relst2register(fr[-1])
    if len(fr)>=3:
        style+=relst2register(fr[1])
        style+=str(int(1+math.floor(3*ti[1])))

    style = ''.join(style)
    return (style,smooth)

def show_stylization(time_org,original,smooth,style,targetIntv,register,figIn,support, is_new_support=True):

    # parameters
    num_time_partitions_per_target = 3
    num_freq_boundaries = 5
    freq_min = -10
    freq_max = +10
    linewidth_RelGrid_Major=.75/3*1
    linewidth_RelGrid_Minor=.375/3/2
    linewidth_LocReg = .75
    linestyle_RelGrid_Major='-'
    linestyle_RelGrid_Minor='-'
    color_RelGrid_Minor = 'yellow'
    
    fig = figIn
    ax = fig.gca()
    
    # put window title
    if is_new_support:
      fig_window_title = u'Figure - Melodic Contour of \'{}\''.format(support.label)
      fig.canvas.set_window_title(fig_window_title)
    # make time axis
    xlim = [sec2msec(time_org[0]),sec2msec(time_org[-1])]
    xticks = np.linspace(xlim[0], xlim[1], num_time_partitions_per_target+1)
    xticks_major = xlim
    xticks_minor = sorted(list(set(xticks) - set(xticks_major)))
    
    if not is_new_support:
        xticks_minor+=list(ax.xaxis.get_ticklocs(minor=True))
        #xticks_minor+=list(ax.xaxis.get_ticklocs(minor=False))
        xticks_major2=list(ax.xaxis.get_ticklocs(minor=False))
        xticks_major2+=xticks_major

    if is_new_support:
        ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(xticks_major))
    else:
        ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(xticks_major2))

    #ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(xticks_major))
    ax.xaxis.set_minor_locator(matplotlib.ticker.FixedLocator(xticks_minor))
    xticks_labels_major = ['{:.0f} ms'.format(x) for x in xticks_major]
    xticks_labels_minor = ['{:.0f}'.format(x) for x in xticks_minor]
    ax.set_xticklabels([],minor=False,fontsize=7)
    #ax.set_xticklabels(xticks_labels_minor,minor=True)
    
    ax.grid(b=True,which='major', axis='x',color=color_RelGrid_Minor,linestyle=linestyle_RelGrid_Major,linewidth=linewidth_RelGrid_Major)
    ax.grid(b=True,which='minor', axis='x',color=color_RelGrid_Minor,linestyle=linestyle_RelGrid_Minor,linewidth=linewidth_RelGrid_Minor)
    yticks_major=[-10,-6,-2,2,6,10]
    yticks_minor=[-8,-4,0,4,8]
    ytick2labels_major = ['{:.0f} Hz'.format(register*semitone2hz(y)) for y in yticks_major]
    ytick2labels_minor = ['{:.0f}'.format(register*semitone2hz(y)) for y in yticks_minor]
    if is_new_support:
          ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(yticks_major))
          ax.yaxis.set_minor_locator(matplotlib.ticker.FixedLocator(yticks_minor))
          ax.set_yticklabels(ytick2labels_major,minor=False)
          ax.set_yticklabels(ytick2labels_minor,minor=True)
    tot_yticks = np.concatenate((yticks_major,yticks_minor))
    ylim = [min(tot_yticks),max(tot_yticks)]
    pl.ylim(ylim)
    
    
    # make 2nd freauency axis
    if is_new_support:
          ax2 = ax.twinx()
          # move the second axis to background
          yticklabels_major = ['{:.0f} ST'.format(f) for f in yticks_major]
          yticklabels_minor = ['{:.0f}'.format(f) for f in yticks_minor]
          ax2.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(yticks_major))
          ax2.yaxis.set_minor_locator(matplotlib.ticker.FixedLocator(yticks_minor))
          ax2.set_yticklabels(yticklabels_major,minor=False)
          ax2.set_yticklabels(yticklabels_minor,minor=True)
          #ax.set_zorder(20) 
          #ax.patch.set_visible(False)

    # grid relative to local regster in bleu lines
    register_local = hz2semitone(np.mean([semitone2hz(f) for f in smooth]))
    for offset in [0,-2,2,-6,6,-10,10]:
        if offset :
            ax.plot(xticks_major,[register_local+offset,register_local+offset], linestyle=linestyle_RelGrid_Minor,color=color_RelGrid_Minor,linewidth=linewidth_RelGrid_Minor,zorder=0)
        else: # i.e. offset = 0
            lnst5=ax.plot(xticks_major,[register_local+offset,register_local+offset], 'y-',linewidth=linewidth_LocReg,zorder=0,linestyle=linestyle_RelGrid_Major)
    
    pl.ylim(min(tot_yticks),max(tot_yticks))
    # draw support 
    if is_new_support:
      supp_intv = sec2msec(support.time)
      supp_org = hz2semitone(support.freq) - hz2semitone(register)
      supp_mark = support.label
    
    # draw target
    target_intv = sec2msec(time_org)
   
    
    # stylization
    alphabet2semitones = {'H': 8, 'h': 4, 'm': 0, 'l' : -4, 'L' : -8} 
    def relativePos2time(Pos, interval): 
          return interval[0] + (int(Pos) - .5) / 3 * (interval[-1]-interval[0])

    f_i = alphabet2semitones[style[0]]
    f_f = alphabet2semitones[style[1]]
    style_intv = [xticks_major[0],xticks_major[-1]]
    style_pitch = [f_i,f_f]
    if len(style) >=4:
          f_p = alphabet2semitones[style[2]]
          t_p = relativePos2time(style[3],xticks_major)
          style_intv.insert(1,t_p)
          style_pitch.insert(1,max([f_p,f_i+2,f_f+2]))

    # 2(+1) essential points
    ti,fr=identifyThreeEssentialPoints(smooth,time=time_org)
    essential_intv = sec2msec(np.array(ti))
    essential_pitch = fr
    #print(ti)
    #print(fr)
    
    if is_new_support:
        lns0=ax.plot(supp_intv,supp_org, 'b.',markersize=2)
    #lns1=ax.plot(target_intv,original,'b',linewidth=2)
    
    lns2=ax.plot(target_intv,smooth,'r',linewidth=.35)
    lns4=ax.plot(essential_intv,essential_pitch,'ro',markersize=3)
    lns3=ax.plot(style_intv,style_pitch,'g',linewidth=1.5)
    
    
    #print(supp_intv)
    if is_new_support:
          tot_intv = np.concatenate((supp_intv,target_intv))
          pl.xlim(min(min(tot_intv),xticks[0]),max(max(tot_intv),xticks[-1]))
          ax.grid(b=True,which='major', axis='y', color='0')
          
    if is_new_support:
          ax.set_ylabel('Frequencey (Hz)')
    
    # annotation
    fig.subplots_adjust(top=0.9,bottom=0.125,left=0.075, right=0.925)
    xlim=ax.get_xlim()
    diff_xlim = max(xlim)-min(xlim)
    diff_ylim = max(ylim)-min(ylim)
    x1 = (xticks_major[0]-xlim[0])/diff_xlim
    x2 = (xticks_major[1]-xlim[0])/diff_xlim
    
    # time label
    ax.annotate('{:.0f} ms'.format(xticks_major[-1]-xticks_major[0]),xy=(x2/2+x1/2,-0.035),xycoords='axes fraction',fontsize=6,horizontalalignment='center')
    
    # interval label and symbolic annotation
    ax.annotate(targetIntv.mark(),xy=(.5*xticks_major[0]+.5*xticks_major[1],-0.13+.04),xycoords=('data','axes fraction'),fontsize=11,fontweight='medium',horizontalalignment='center',fontstyle='italic')
    ax.annotate(style,xy=(.5*xticks_major[0]+.5*xticks_major[1],-0.19+.04+.01),xycoords=('data','axes fraction'),fontsize=11,fontweight='semibold',horizontalalignment='center')
    
    if is_new_support:
      ax.annotate(supp_mark,xy=(0.5,1.05),xycoords='axes fraction',fontsize=11,fontweight='medium',  horizontalalignment='center',fontstyle='italic')
      
      ax2.legend(lns3+lns4+lnst5+lns2+lns0,\
      ['Stylized + Smoothed Pitch',\
      'Essential Points of Smoothed Pitch',\
      'Local Register of Smoothed Pitch',\
      'Smoothed Pitch (LOWESS)',\
      'Input Pitch'],fontsize=7)

    # let us make the figure!
    return fig

"""
def stylizeObject(target,swipeFile, speakerTier=None,registers=None,stylizeFunction=SLAM1,estimate_mode=1):

    targetIntv = target

    #get stylization for an object that implements the xmin() and xmax() methods.
    [times_C,pitchs_C] = intv2pitch(target,swipeFile)

    #skipping interval (unvoiced)
    if len(pitchs_C)<2: return ('_',[],[],[],[],[],[])

    #get corresponding interval in the speaker (i.e. support) tier
    [optSpeaker,optIntv, candiateIntvs] = getMaxMatchIntv([targetIntv],speakerTier)

    speaker = optSpeaker
    speakers_intervals=candiateIntvs

    #if estimate_mode == 2:
    if True:
        print('========== EXPERIMENT START ====')
        #get temporal indices
        #for target
        imin,imax = swipeFile.time_bisect(target.xmin(),target.xmax())
        if imin < imax: upper_bound = imax
        else: upper_bound = imax + 1
        target_int = range(imin,upper_bound)
        #for support
        support_int = []
        for i in speakers_intervals:
            if i.mark() == speaker:
                imin,imax = swipeFile.time_bisect(i.xmin(),i.xmax())
                if imin < imax: upper_bound = imax
                else: upper_bound = imax + 1
                support_int += range(imin,upper_bound)
        #get the temporal index of
        #the center of intersection of the support and the target
        inter = list(set(target_int) & (set(support_int)))
        center = inter[len(inter) // 2]

        #estimate register using Hann window
        r = 0.0
        c = 0.0
        half_width = max(center - support_int[0] + 1, support_int[-1] - center + 1)
        for t in support_int:
            #compute a Hann window
            w = 0.0
            #convoluate it with a rectangular function with its support as our target
            for center_mobile in inter:
                w += (np.cos(np.pi / 2.0 / float(half_width) * (t - center_mobile))) ** 2
            #w = 1 #debug: constant window
            r += w * swipeFile.pitch[t]
            c += w
        if c: r = r / c # normalization

    #get corresponding register value
    if not registers:
        #if a speaker tier is provided and registers is not already computed,
        #compute it.
        registers = averageRegisters(swipeFile,speakerTier)

    if speaker:
        #reference is the value of the registers for this speaker
        reference = registers[speaker]
        if not reference: return ('',[],[],[],[],[],[]) #bugfix
    else: #speaker == None
        if not is_numeric_paranoid(registers):
            print('WARNING : no speaker tier provided and reference is not numeric ! not stylizing.')
            return ('',[],[],[],[],[],[])
        #no speaker/support tier was provided, registers is only the average f0
        reference = registers

    if estimate_mode == 2:
        try:
            print('(new register, old register,diff): ({},{},{})'.format(r,reference, abs(r-reference)))
        except:
            print('(new register, old register): ({},{})'.format(r,reference))
            print(registers)
            exit(1)
        reference = r
        print('========== EXPERIMENT END ======')


    #delta with reference in semitones
    delta_pitchs_C = [(hz2semitone(pitch) - hz2semitone(reference)) for pitch in pitchs_C]
    (style,smoothed) = stylizeFunction(delta_pitchs_C,tier=target,register=reference)

    smoothed_out = [cent2hz((100*delta + hz2cent(reference))) for delta in smoothed]
    #print(reference)
    supportIntv = intv2pitch(optIntv,swipeFile)
    supportIntv.append(optIntv.mark())
    return (style,delta_pitchs_C,smoothed,times_C, smoothed_out, reference,supportIntv)

"""

def stylizeObject(targetIntv,supportIntv,inputPitch,registers,stylizeFunction=SLAM1):

    #get stylization for an object that implements the xmin() and xmax() methods.
    [targetTimes,targetPitch] = intv2pitch(targetIntv,inputPitch)
    
    #do not process if no enough of sample
    if len(targetPitch)<2:
          return None
        
    #get valide reference
    if is_numeric_paranoid(registers): 
          #no speaker/support tier was provided, registers is only the average f0
          reference = registers
    else:
          try:
              reference = registers[supportIntv.mark()]
              if not is_numeric_paranoid(reference):
                    raise
          except:
              #fail to get valide reference before precceding stylization
              return None
    
    #delta with reference in semitones
    deltaTargetPitch = [(hz2semitone(pitch) - hz2semitone(reference)) for pitch in targetPitch]
    
    #stylize if sample length enough 
    (style,smoothed) = stylizeFunction(deltaTargetPitch)
    
    return (style,targetTimes,deltaTargetPitch,smoothed,reference)

# source:
# https://stackoverflow.com/questions/500328/identifying-numeric-and-array-types-in-numpy
def is_numeric_paranoid(obj):
    try:
        obj+obj, obj-obj, obj*obj, obj**obj, obj/obj
    except ZeroDivisionError:
        return True
    except Exception:
        return False
    else:
        return True

def getSupportIntv(targetIntv,supportTier):
      
      """
      this function returns the interval of 'supportTier' which 
      matchs the best with the given 'targetIntv'. 
      
      inputs
            targetIntv
            supportTier
      return
            supportIntv
      """

      trgt,spprt = targetIntv,supportTier #alias
      supportIntvs = tg.getMatchingIntervals([trgt],spprt,strict=False,just_intersection=True)
      labels = [intv.mark() for intv in supportIntvs]
      labelsCount = dict((label,labels.count(label)) for label in set(labels))
      bestLabel = max(labelsCount,key=labelsCount.get)
      for intv in supportIntvs:
          if intv.mark() == bestLabel:
              return intv
                    
def printIntv(intv):
        
      """
      convinient function to shwo the content of an 'interval' 
      objet defined in 'TextGrid' class
      """
      print('{}: [{},{}]'.format(intv.mark().encode('utf-8'),intv.xmin(),intv.xmax()))
            
class intv2customPitchObj():
      
      """
      convinient class which converts an 'interval' objet to
      a class having the 3 follwing attributes: time, freq, label
      which is useful for tracing figure
      """
      
      def __init__(self,supportIntv, inputPitch):
            self.label=supportIntv.mark()
            [self.time,self.freq]=intv2pitch(supportIntv,inputPitch)

#handy funciotns
def get_extension(file): return os.path.splitext(file)[1]
def get_basename(file): return os.path.splitext(os.path.basename(file))[0]

#read a PitchTier as swipe file
class readPitchtier(swipe.Swipe):
	def __init__(self, file):
                try:
		    [self.time, self.pitch] = praatUtil.readBinPitchTier(file)
                except:
		    [self.time, self.pitch] = praatUtil.readPitchTier(file)

def hz2cent(f0_Hz):
    return 1200.0*np.log2( np.maximum(1E-5,np.double(f0_Hz) ))
def cent2hz(semitone):
    return np.double(2.0**(np.double(semitone) / 1200.0))
def hz2semitone(f0_Hz):
    return 12.0*np.log2( np.maximum(1E-5,np.double(f0_Hz) ))
def semitone2hz(semitone):
    return np.double(2.0**(np.double(semitone) / 12.0))
def sec2msec(sec):
    return 1000.0 * sec

def relst2register(semitones):
    #from relative semitones to register
    if isinstance(semitones,(int,float)):
        semitones = [semitones]
    result = []
    for st in semitones:
        if   st > 6  : result.append('H')
        elif st > 2  : result.append('h')
        elif st > -2  : result.append('m')
        elif st > -6  : result.append('l')
        elif st < -6  : result.append('L')
    return result

def averageRegisters(swipeFile,speakerTier=None):
    #if no speaker tier is provided, just take the average of the f0s
    if speakerTier is None:
        print('     No speaker tier given, just taking mean of f0s as average register')
        pitchs = [x for x in swipeFile if x]
        return np.mean(pitchs)

    #get all different speaker names
    speakerNames = set([interval.mark() for interval in speakerTier])
    registers     = {}
    #for each speaker, compute mean register
    for speaker in speakerNames:
        intervals = [interval for interval in speakerTier if interval.mark()==speaker]
        #on va calculer la moyenne=sum/n
        sumf0 = 0
        nf0 = 0
        for interval in intervals:
            imin, imax = swipeFile.time_bisect(interval.xmin(),interval.xmax())
            pitchs = [x for x in swipeFile.pitch[imin:imax] if x]
            sumf0 += np.sum(pitchs)
            nf0  += len(pitchs)
        if nf0:
            registers[speaker]=sumf0/np.double(nf0)
        else:
            registers[speaker]=None
    return registers
    

def identifyThreeEssentialPoints(freq,time=None, thld=2):
    #assume data is of increasing order of time
    try:
        t = [time[0],time[-1]]
    except TypeError:
        time = np.linspace(0, 1, len(freq))
        t = [time[0],time[-1]]
    #t = [time[0],time[-1]]
    f = [freq[0],freq[-1]]
    k = (np.array(freq)).argmax()
    maximum = freq[k]
 
    if all((maximum - np.array(f)) > thld): 
          t.insert(1,time[k])
          f.insert(1,maximum)
    return t,f

def intv2pitch(intv,swipeFile):
    imin, imax = swipeFile.time_bisect(intv.xmin(),intv.xmax())
    pitch = swipeFile.pitch[imin:imax]
    time = swipeFile.time[imin:imax]
    return [time,pitch]

def getMaxMatchIntv(target,support):
    candidateIntvs = tg.getMatchingIntervals(target,support,strict=False,just_intersection=True)
    marks = [intv.mark() for intv in candidateIntvs]
    marksCount = dict( (mark,marks.count(mark)) for mark in set(marks))
    #counting the speakers
    if len(marksCount)>1:
        optMark = max(marksCount,key=marksCount.get)
        print('     Keeping %s'%optMark, marksCount)
    else:
        #only one speaker for all target intervals
        optMark = marks[0]
    optIntv = [intv for intv in candidateIntvs if intv.mark() == optMark][0]
    return optMark, optIntv, candidateIntvs