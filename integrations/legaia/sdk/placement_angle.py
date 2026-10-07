"""Deterministic Q30 whole-degree X/Z position rotation; never actor facing."""
from .project import ProjectError
Q=1<<30
SIN_QUARTER=[0, 18739379, 37473049, 56195305, 74900443, 93582766, 112236583, 130856211, 149435979, 167970228, 186453311, 204879599, 223243478, 241539355, 259761657, 277904834, 295963357, 313931728, 331804471, 349576144, 367241333, 384794656, 402230767, 419544355, 436730145, 453782903, 470697435, 487468587, 504091252, 520560366, 536870912, 553017922, 568996477, 584801711, 600428808, 615873009, 631129609, 646193961, 661061475, 675727625, 690187940, 704438018, 718473518, 732290163, 745883746, 759250125, 772385229, 785285058, 797945680, 810363241, 822533958, 834454122, 846120104, 857528349, 868675383, 879557810, 890172315, 900515665, 910584710, 920376381, 929887697, 939115760, 948057759, 956710970, 965072759, 973140576, 980911966, 988384560, 995556083, 1002424350, 1008987269, 1015242840, 1021189159, 1026824413, 1032146887, 1037154959, 1041847103, 1046221891, 1050277989, 1054014162, 1057429273, 1060522280, 1063292242, 1065738315, 1067859754, 1069655912, 1071126243, 1072270298, 1073087729, 1073578288, 1073741824]

def sine(angle):
    n=angle%360;quadrant,offset=divmod(n,90)
    return (SIN_QUARTER[offset] if quadrant==0 else SIN_QUARTER[90-offset] if quadrant==1 else -SIN_QUARTER[offset] if quadrant==2 else -SIN_QUARTER[90-offset])

def rotate_position(position,pivot,step,degrees):
    if type(degrees) is not int or not -359<=degrees<=359:
        raise ProjectError('Position rotation requires whole degrees from -359 through 359')
    if type(step) is not int or step not in (1,64) or any(type(p[a]) is not int or abs(p[a])>1048576 for p in (position,pivot) for a in ('x','z')):
        raise ProjectError('Angle rotation requires bounded integer Current X/Z coordinates')
    s,c=sine(degrees),sine(degrees+90);dx,dz=position['x']-pivot['x'],position['z']-pivot['z']
    numerators={'x':pivot['x']*Q+dx*c-dz*s,'z':pivot['z']*Q+dx*s+dz*c};denominator=Q*step
    return {a:(-1 if n<0 else 1)*((abs(n)+denominator//2)//denominator)*step for a,n in numerators.items()}
