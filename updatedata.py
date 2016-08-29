#!/usr/local/bin/python
import requests
import json
import sys
from subprocess import call

allPlayers=[]

def readsettings(settingsfilename):
    file=open(settingsfilename)
    retval=json.loads(file.read())
    return retval

def getURLJSON(url,cachefilename):
    #for some reason fantasysharks works in wget, but not with curl or requests
    #TODO: implement caching to only redownload if it has been more than an hour
    #call(["wget", url, "-O",cachefilename])

    file=open(cachefilename)
    retval=json.loads(file.read())
    return retval


def getIDPPlayers():
    players=getURLJSON("http://www.fantasysharks.com/apps/Projections/SeasonProjections.php?pos=ALLIDP&format=json","idp.json")
    #print json.dumps(players, indent=4)
    return players

def getSTDPlayers():
    players=getURLJSON("http://www.fantasysharks.com/apps/Projections/SeasonProjections.php?pos=ALL&format=json&l=1","std.json")
    #print json.dumps(players, indent=4)
    return players
def getPKPlayers():
    players=getURLJSON("http://www.fantasysharks.com/apps/Projections/SeasonProjections.php?pos=PK&format=json&l=1","pk.json")
    #print json.dumps(players, indent=4)
    return players

def scoreSTDPlayers(stdplayers,settings,pos):
    if settings["num"+pos]<1:
        return
    global allPlayers
    posplayers=[]
    for player in stdplayers:
        if player["Pos"]==pos:
            projScore=0
            projScore+=int(player["PassYards"])/settings["PassYdsPerPt"]
            projScore+=int(player["PassTD"])*settings["PtsPassTD"]
            projScore+=int(player["Int"])*settings["PtsPassInter"]
            projScore+=int(player["RushYards"])/settings["RushYdsPerPt"]
            projScore+=int(player["RushTD"])*settings["PtsRushTD"]
            projScore+=int(player["Fum"])*settings["PtsFumLost"]
            projScore+=int(player["Rec"])*settings["PtsRec"]
            projScore+=int(player["RecYards"])/settings["RecYdsPerPt"]
            projScore+=int(player["RecTD"])*settings["PtsRecTD"]
            #print "%s: %d"%(player["Name"],projScore)
            player["projScore"]=projScore
            posplayers.append(player)
    posplayers.sort(key= lambda player: player["projScore"],reverse=True)
    minstarting=posplayers[settings["numTeams"]*settings["num"+pos]-1]["projScore"]
    maxvalue=posplayers[0]["projScore"]-minstarting
    #print "MAX VALUE %s: %d numStarters %d" % (pos,maxvalue,settings["numTeams"]*settings["num"+pos])
    for player in posplayers:
        player["value"]=player["projScore"]-minstarting
        player["aPos"]=pos;
        allPlayers.append(player)


def defTypeMatch(Pos,group,settings):
    if (group=="DB" and (Pos=="S" or Pos=="CB")):
        if settings["num"+group]<1:
            return False
        return True
    if (group=="LB" and (Pos=="LB")):
        if settings["num"+group]<1:
            return False
        return True
    if (group=="DL" and (Pos=="DT" or Pos=="DE")):
        if settings["num"+group]<1:
            return False
        return True
    return False

def scoreIDPPlayers(idpplayers,settings,pos):
    global allPlayers
    posplayers=[]
    for player in idpplayers:
        if (defTypeMatch(player["Pos"],pos,settings)):
            projScore=0
            projScore+=int(player["Sacks"])*settings["PtsDEFSack"]
            projScore+=int(player["FumForced"])*settings["PtsDEFFFum"]
            projScore+=int(player["FumRecovered"])*settings["PtsDEFFumRec"]
            projScore+=int(player["Int"])*settings["PtsDEFInter"]
            projScore+=int(player["PassDef"])*settings["PtsPassDef"]
            projScore+=int(player["Tackles"])*settings["PtsDEFsoloTac"]
            projScore+=int(player["Assists"])*settings["PtsDEFassTac"]
            projScore+=int(player["TD"])*settings["PtsDEFTD"]
            #print "%s: %d"%(player["Name"],projScore)
            player["projScore"]=projScore
            posplayers.append(player)
    posplayers.sort(key= lambda player: player["projScore"],reverse=True)
    minstarting=posplayers[settings["numTeams"]*settings["num"+pos]-1]["projScore"]
    maxvalue=posplayers[0]["projScore"]-minstarting
    #print "MAX VALUE %s: %d numStarters %d" % (pos,maxvalue,settings["numTeams"]*settings["num"+pos])
    for player in posplayers:
        player["value"]=player["projScore"]-minstarting
        player["aPos"]=pos;
        allPlayers.append(player)

def scorePKPlayers(pkplayers,settings,pos):
    if settings["num"+pos]<1:
        return
    global allPlayers
    posplayers=[]
    for player in pkplayers:
        player["projScore"]=int(player["FantasyPoints"])
        posplayers.append(player)
    posplayers.sort(key= lambda player: player["projScore"],reverse=True)
    minstarting=posplayers[settings["numTeams"]*settings["num"+pos]-1]["projScore"]
    maxvalue=posplayers[0]["projScore"]-minstarting
    #print "MAX VALUE %s: %d numStarters %d" % (pos,maxvalue,settings["numTeams"]*settings["num"+pos])
    for player in posplayers:
        player["value"]=player["projScore"]-minstarting-settings["SubtractFromPKValue"]
        player["aPos"]=pos;

        allPlayers.append(player)

def printplayers(allPlayers):
    myRank=1
    for player in allPlayers:
        print '%d,"%s","%s","%s",%s,%d' % (myRank,player["Name"],player['Team'],player['aPos'],player['ADP'],player['value'])
        myRank=myRank+1

if len(sys.argv)<2:
    sys.exit("usage: %s configfile.json"%sys.argv[0])


settings=readsettings(sys.argv[1])

idpplayers=getIDPPlayers()
stdplayers=getSTDPlayers()
pkplayers=getPKPlayers()

scoreSTDPlayers(stdplayers,settings,"QB")
scoreSTDPlayers(stdplayers,settings,"RB")
scoreSTDPlayers(stdplayers,settings,"WR")
scoreSTDPlayers(stdplayers,settings,"TE")
scorePKPlayers(pkplayers,settings,"PK")
scoreIDPPlayers(idpplayers,settings,"DL")
scoreIDPPlayers(idpplayers,settings,"LB")
scoreIDPPlayers(idpplayers,settings,"DB")

allPlayers.sort(key= lambda player: player["value"],reverse=True)
#print json.dumps(allPlayers, indent=4)
printplayers(allPlayers)
