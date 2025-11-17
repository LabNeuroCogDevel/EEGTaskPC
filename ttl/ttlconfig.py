class TTLConfig():
    """Customizations on how to handle values.
    potentially useful if status channel values can be simplified/rewritten"""
    @staticmethod
    def ttl_convert(x):
        return x
    @staticmethod
    def discard(x, maxdiff):
        return x[x<maxdiff]

    #: a,b, and label. example for eyes open block of rest
    betweens = [{'a': 200, 'b': 201, 'label': 'block'}]
    maxdiff = 10000


class Habit(TTLConfig):
    """Habit has a ton of information.
    We only care about 3 phases for timing/trial check."""
    @staticmethod
    def ttl_convert(ttl):
        if ttl == 1: # photo diode
            return 1
        elif ttl < 10: # button push 2,3,4
            return 2
        elif ttl == 10:
            return 10
        elif ttl < 100: # 10 20
            return (ttl // 10)  * 10
        elif ttl > 100:
            return (ttl // 100)  * 100

    betweens = [{'a': 10, 'b': 100, 'label': 'rt'},
                {'a': 2,  'b': 1, 'label': 'bnt2pd'} ]

class VGSAnti(TTLConfig):
    """VGS enclose position but we can discared that for the sake of timing

     ./lpt_timing.py -v /Volumes/Hera/Raw/EEG/SPA/12184_20251105/12184_20251105_anti.bdf
     [[  101   102   104   105   151   152   154   155   254 65664]
      [   10    10    10    10    10    10    10    10    40     1]]
     ./lpt_timing.py -v /Volumes/Hera/Raw/EEG/SPA/12184_20251105/12184_20251105_vgs.bdf
     [[    1     2     4     5    51    52    54    55   254 65664 65790]
      [   10    10    10    10    10    10    10    10    40     1     1]]
    """
    @staticmethod
    def ttl_convert(ttl):
        if ttl < 10 or (ttl > 100 and ttl < 110):
            return 10
        elif (ttl > 50 and ttl < 100) or (ttl > 150 and ttl < 200):
            return 50
        else: #ttl > 200:
            return ttl
        
    betweens = [{'a': 10, 'b': 254, 'label': 'trial'},
                #{'a': 100, 'b': 10, 'label': 'cue'}
                ]

class Rest(TTLConfig):
    """
    """
    maxdiff = 8
    betweens = [{'a': 2, 'b': None, 'label': 'openpulse'},
                {'a': 1, 'b': None, 'label': 'closepulse'},
                ]
class Switch(TTLConfig):
    """
    ttls
    iti:        10 
    cue       : 51 (cog)    52  (incong)
    cong      : 101   102   103  
    semi 1 cor: 211 to 216
    semi 2 cor: 221 to 226
    semi 3 cor: 231 to 236
    buttons   : 2     3     4 
    anything else: 250
    """
    def ttl_convert(ttl):
        if ttl == 10:
            return 10       # 10 = iti
        if ttl in [51, 52]:
            return 50       # 50  = "+" trial cue
        elif ttl > 100 and ttl < 250:
            return 200      # 200 = see numbers
        if ttl < 10:
            return 1        # 1 = button push
        return ttl          # 250 is what?

    # rt tells us if button box was working
    betweens = [{'a': 1, 'b': 10, 'label': 'push2flip'}, # this is wildly variable ~ .03s
                {'a': 50, 'b': 200, 'label': 'cue2num'},
                {'a': 200, 'b': 1, 'label': 'rt'},
                ]

class DollarReward(TTLConfig):
    """
Trigger values look like
[[   50   130   131   132   133   134   135   136   141   142   143   144
    145   146   230   231   232   233   234   235   236   241   242   243
    244   245   246 65586 65664]
 [  142     3     3     2     2     2     3     3     3     2     2     2
      3     3     3     3     2     2     2     1     3     3     2     2
      2     1     3     1     1]]
    """
    def ttl_convert(ttl):
        if ttl == 50:
            return 50       # 50 = iti
        elif ttl < 200:
            return 100      # 100 = cue? side+rew/neu
        if ttl > 200 and ttl < 255:
            return 200      # 200 = dot? side+rew/neu
        return ttl          # junk?

    betweens = [{'a': 50,  'b': 100, 'label': 'iti2cue'},
                #{'a': 100, 'b': 200, 'label': 'cue2dot'},
                {'a': 200, 'b': 50,  'label': 'dot2iti'}]

class SteadyState(TTLConfig):
    """
    """
    betweens = [{'a': 2, 'b': None, 'label': 'ss pulse'}]

class EyeCal(TTLConfig):
    """
    Each position has it's own trigger.
    We care about time between them. so set all to be the same
    """
    @staticmethod
    def ttl_convert(ttl):
        if ttl < 100:
            return 100
        elif ttl < 255:
            return 200
        return ttl

    betweens = [{'a': 100, 'b': 200, 'label': 'dot'}]
