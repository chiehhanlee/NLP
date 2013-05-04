#! /usr/bin/python
import sys
import re
import json

__author__="Chiehhan Lee<chiehhanlee.gmail.com>"
__date__ ="$Mar 11, 2013"

RARE_CNT = 5

IS_TAG_EXTENSION = 0

OVERFLOW_TUNING = 4

RARE_TOKEN      ='_RARE_'
NUMERTIC_TOKEN  ='_NUM_'
ALL_CAP_TOKEN   ='_ALL_CAP_'
LAST_CAP_TOKEN  ='_LAST_CAP_'


STOP_TOKEN = 'STOP'
INIT_TOKEN = '*'
NONE_TOKEN = '_NONE_'


def BuildWM(iFile,wm):
    """
    Build Word Maps for tag and count
    """
    for line in iFile:
        line = line.strip()
        li = str(line).split(' ')
        cnt = int(li[0]) #Counter
        tt = li[1]  #Tag Type
        tag = li[2] #Tag
        if tt=='UNARYRULE':
            word = li[3] 
            if(word in wm):
                wm[word].update({tag:cnt})
            else:
                wm[word]={tag:cnt}
#        if tt=='1-GRAM':
#            ug[tag]=cnt
#        if tt=='2-GRAM':
#            ct = li[3] #cur tag
#            if(ct in bg):
#                bg[ct].update({tag:cnt})
#            else:
#                bg[ct]={tag:cnt}
#        if tt=='3-GRAM':
#            pt = li[3] #pre tag
#            ct = li[4] #cur tag
#            if(ct in tg):
#                if pt in tg[ct]:
#                    tg[ct][pt].update({tag:cnt})
#                else:
#                    tg[ct][pt]={tag:cnt}
#            else:
#                tg[ct]={pt:{tag:cnt}}
    
   
    wm[STOP_TOKEN]={'STOP':1}
    wm[INIT_TOKEN]={'*':1}

def BuildTM(wm,tm):
    """
    Build Tags Maps for words and count
    """
    for w in wm:
        for tag , cnt in wm[w].iteritems():
            if(tag in tm):
                tm[tag].update({w:cnt})
            else:
                tm[tag]={w:cnt}

def GetTagCnt(tm,tag):
    cnt=0
    if tag in tm:
        for w in tm[tag]:
            cnt += tm[tag][w]
    return cnt            

def PrintMap(wm):
    """
    Print Map for Debug
    """
    for i in wm:
        print i
        for j,Cnt in wm[i].iteritems():
            print '\t('+j+','+str(Cnt)+')'
        print ''

def SearchRareToken(wm,word):
    isRare=0
    if not word in wm:
        isRare=1
    else:
        wCnt=0
        for wt in wm[word]:
            wCnt += wm[word][wt]
        if wCnt < RARE_CNT :
            isRare=1
    if isRare ==1:
        if IS_TAG_EXTENSION:
            if re.match('.*[0-9]+.*',word):
                return NUMERTIC_TOKEN
            if re.match('^[A-Z]+$',word):
                return ALL_CAP_TOKEN
            if re.match('.*[A-Z]+$',word):
                return LAST_CAP_TOKEN
        return RARE_TOKEN
    return word


def AssignTagUni(tFile,wm,tm):
    """
    Using Uni-GRAM Method to Tagging the sequence
    """
    tc = dict()
    for tag in tm:
        tc.update({tag:GetTagCnt(tm,tag)})
    for line in tFile:
        line = line.strip()
        if(len(line) ==0):
            print ' '
            continue
        li = str(line).split(' ')
        word = li[0] 
        dw = SearchRareToken(wm,word) # Dictionary Word for look up
        p=0
        tokenTag='NONE'
        for tag in tm:
            if dw in tm[tag]:
                cur = float(tm[tag][dw])/tc[tag]
                if cur > p:
                    p = cur
                    tokenTag = tag
        if tokenTag =='NONE':
            sys.stderr.write('ASSERT, CANT FIND TAG')
        print word,tokenTag

def AssignTagTri(tFile,wm,tm,ug,bg,tg):
    """
    Using Tri-GRAM Method to Tagging the sequence
    """
    tc = dict()
    for tag in tm:
        tc.update({tag:GetTagCnt(tm,tag)})
    tag[0] = '*' #Cur-Tag
    tag[1] = '*' #Pre-Tag
    tag[2] = '*' #Pre-Pre Tag
    for line in tFile:
        line = line.strip()
        if(len(line) ==0):
            tag[0] = '*' #Cur-Tag
            tag[1] = '*' #Pre-Tag
            tag[2] = '*' #Pre-Pre Tag
            print ' '
            continue
        li = str(line).split(' ')
        word = li[0] 
        dw = SearchRareToken(wm,word)
        p=0
        tokenTag='NONE'
        for tag in tm:
            if dw in tm[tag]:
                cur = float(tm[tag][dw])/tc[tag]
                if cur > p:
                    p = cur
                    tokenTag = tag
        if tokenTag =='NONE':
            sys.stderr.write('ASSERT, CANT FIND TAG')
        print word,tokenTag

def TraverseWords(Node,wm):
    if len(Node) == 2: # Undary Node
        cnts =0
        if Node[1] in wm:
            for tag , cnt in wm[Node[1]].iteritems():
                cnts += cnt
        if cnts < RARE_CNT:
            Node[1] = RARE_TOKEN
    else:              # Binary Node
        TraverseWords(Node[1],wm)
        TraverseWords(Node[2],wm)

def MarkRareToken():
    wm = dict()
    with open(sys.argv[1],'r') as CntFile:
        BuildWM(CntFile,wm) 
        with open(sys.argv[2],'r') as sFile:
            for line in sFile:
                slist = json.loads(line)
                TraverseWords(slist,wm)
                print json.dumps(slist)

def TagUniGram():
    wm = dict()
    tm = dict()
    ug = {}
    bg = {}
    tg = {}
    with open(sys.argv[1],'r') as CntFile:
        BuildWM(CntFile,wm,ug,bg,tg) 
        BuildTM(wm,tm) 
        with open(sys.argv[2],'r') as tFile:
            AssignTagUni(tFile,wm,tm)

def ViterbiAlgo(sen,wm,tm,bg,tg,rSen):

    tc = dict()
    for tag in tm:
        tc.update({tag:GetTagCnt(tm,tag)})

    pi=[0]*len(sen)
    bp=[0]*len(sen)

    pi[1]={INIT_TOKEN : {INIT_TOKEN : 1}}

    for k in range(2,len(sen)):
        pi[k]={}
        bp[k]={}
        for v in tg.keys(): 
            pi[k][v]={}
            bp[k][v]={}
            if not v in wm[sen[k]].keys():
                continue
            for u in tg[v].keys():
                maxq   = 0
                maxarg = NONE_TOKEN
                if not u in pi[k-1]:
                    continue
                for w in tg[v][u].keys():
                    q=0
                    if w in pi[k-1][u]:
                        q = float(pi[k-1][u][w])\
                                *(float(wm[sen[k]][v])/tc[v])\
                                *(float(tg[v][u][w])/bg[u][w])*OVERFLOW_TUNING
                        if q == 0:
                            sys.stderr.write('WARNNING : OVERFLOW at '+str(k)+'/'+str(len(sen))+'\n')
                    if q > maxq:
                        maxq = q
                        maxarg = w                        
                if maxq ==0:
                    continue
                pi[k][v][u] = maxq
                bp[k][v][u] = maxarg

    maxq = 0
    tl=[0]*(len(sen))
    tl[len(sen)-1]=STOP_TOKEN
    
    k = len(sen)-1
    for u in pi[k][STOP_TOKEN]:
        if maxq < pi[k][STOP_TOKEN][u]:
            maxq =  pi[k][STOP_TOKEN][u]
            tl[k-1]=u

    if maxq == 0 :
        sys.stderr.write('NO VALID TAG SEQ')
        print sen
        sys.exit(2)
        return

    for k in reversed(range(2,len(sen)-2)):
        tl[k]=bp[k+2][tl[k+2]][tl[k+1]]
    
    for idx in range(2,len(sen)-1):
        print rSen[idx], tl[idx]

    print ''

def TagTriGram():
    wm = dict()
    tm = dict()
    ug = {}
    bg = {}
    tg = {}
    with open(sys.argv[1],'r') as CntFile:
        BuildWM(CntFile,wm,ug,bg,tg) 
        BuildTM(wm,tm) 
        with open(sys.argv[2],'r') as tFile:
            rSen=[INIT_TOKEN,INIT_TOKEN]  # Raw Sentence
            mSen=[INIT_TOKEN,INIT_TOKEN]  # Remaped Sentence
            for line in tFile:
                line = line.strip()
                if(len(line) ==0):
                    rSen.append(STOP_TOKEN)
                    mSen.append(STOP_TOKEN)
                    ViterbiAlgo(mSen,wm,tm,bg,tg,rSen)
                    rSen=[INIT_TOKEN,INIT_TOKEN]
                    mSen=[INIT_TOKEN,INIT_TOKEN]
                    continue
                li = str(line).split(' ')
                dw = li[0] #Dictionart Word
                rSen.append(dw)
                dw = SearchRareToken(wm,dw)
                mSen.append(dw)


if __name__ == "__main__":
    if len(sys.argv)!=3:# Expect exactly one argument: the training data file
        sys.stderr.write('Input Parameter Num Error')
        sys.exit(2)

    MarkRareToken()
    #TagTriGram()
    
