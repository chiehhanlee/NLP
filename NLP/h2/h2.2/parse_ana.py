#! /usr/bin/python
import sys
import re
import json
from math import log

__author__="Chiehhan Lee<chiehhanlee.gmail.com>"
__date__ ="$April 11, 2013"

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

TOTAL_TOKEN = '_TOTAL_'

def BuildWM(iFile,wm,tm,mm):
    """
    Build Word Maps for tag and count
    """
    for line in iFile:
        line = line.strip()
        li  = str(line).split(' ')
        cnt = int(li[0]) #Counter
        tt  = li[1]  #Tag Type
        tag = li[2] #Tag
        if tt=='UNARYRULE':
            word = li[3] 
            if not (word in wm):
                wm[word]={TOTAL_TOKEN:0}
            wm[word].update({tag:cnt})
            wm[word][TOTAL_TOKEN] += cnt

        if tt=='NONTERMINAL':
            tm[tag]=cnt
        if tt=='BINARYRULE':
            mt1 = li[3] #map tag 1
            mt2 = li[4] #map tag 2
            if(tag in mm):
                mm[tag].update({(mt1,mt2):cnt})
            else:
                mm[tag]={(mt1,mt2):cnt}


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

def TraverseWords(Node,wm):
    if len(Node) == 2: # Undary Node
        Node[1] = SearchRareToken(wm,Node[1])
    else:              # Binary Node
        TraverseWords(Node[1],wm)
        TraverseWords(Node[2],wm)

def MarkRareToken():
    wm = {} #word map
    tm = {} #tag map
    mm = {} #map map
    
    with open(sys.argv[1],'r') as CntFile:
        BuildWM(CntFile,wm,tm,mm) 
        with open(sys.argv[2],'r') as sFile:
            for line in sFile:
                slist = json.loads(line)
                TraverseWords(slist,wm)
                print json.dumps(slist)

def TravaseParserTree(bp,fr,to,tag):
    if type(bp[fr][to][tag])==tuple:
        s,mt1,mt2 = bp[fr][to][tag]
        tree    =[0]*3
        tree[0] = tag
        tree[1] = TravaseParserTree(bp,fr,s,mt1)
        tree[2] = TravaseParserTree(bp,s+1,to,mt2)
    else:
        tree    =[0]*2
        tree[0] = tag
        tree[1] = bp[fr][to][tag]
    return tree


def ParseSentence():
    wm = {} #word map
    tm = {} #tag map
    mm = {} #map map
    with open(sys.argv[1],'r') as CntFile:
        BuildWM(CntFile,wm,tm,mm) 
        with open(sys.argv[2],'r') as sFile:
            for line in sFile:
                sen = line.strip().split(' ')
                n = len(sen)
                #Initialize Table
                pi = [None] * n
                bp = [None] * n
                for i in range(n):
                    pi[i] = [None] * n
                    bp[i] = [None] * n
                    for j in range(i,n):
                        pi[i][j]={}
                        bp[i][j]={}

                    word = SearchRareToken(wm,sen[i])
                    for tag in wm[word]:
                        if tag != TOTAL_TOKEN:
                            pi[i][i][tag] = log(wm[word][tag]) - log(wm[word][TOTAL_TOKEN])
                            bp[i][i][tag] = sen[i]
                #Building Table
                for l in range(1,n):
                    for i in range(n-l):
                        j = i + l
                        for NT in tm: # Non-Terminal
                            if not NT in mm:
                                continue
                            maxpi=None
                            arg = None
                            for s in range(i,j):
                                for mp , cnt in mm[NT].iteritems():
                                    mt1 , mt2 = mp
                                    cur = None
                                    if mt1 in pi[i][s] and mt2 in pi[s+1][j]:
                                        cur = pi[i][s][mt1] + pi[s+1][j][mt2] + log(cnt) - log(tm[NT])
                                    if cur > maxpi:
                                        maxpi = cur
                                        arg   = (s,mt1,mt2)
                            if maxpi != None:
                                pi[i][j][NT] = maxpi
                                bp[i][j][NT] = arg
                #Back Track the Parser Tree
                if 'SBARQ' in bp[0][n-1]:
                    tree = TravaseParserTree(bp,0,n-1,'SBARQ')
                else:
                    sys.stderr.write("SENTENCE CAN NOT BE PARSED")
                    maxtag = None
                    mx = None
                    for tag in pi[i][j]:
                        if pi[i][j][tag] > mx:
                            mx = pi[i][j][tag]
                            maxtag = tag
                    tree = TravaseParserTree(bp,0,n-1,tag)
                print json.dumps(tree)


if __name__ == "__main__":
    if len(sys.argv)!=3:# Expect exactly one argument: the training data file
        sys.stderr.write('Input Parameter Num Error')
        sys.exit(2)

    #MarkRareToken()
    ParseSentence()

