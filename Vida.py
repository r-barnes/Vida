#!/usr/bin/env python
"""This file is part of Vida.
--------------------------
Copyright 2017, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""
vidaVersion = "0.9.0.2"

import random
import math
import os
import os.path
import glob
import sys
import argparse
import configparser


import copy
import time
import pickle
###append the path to basic data files
sys.path.append("Vida_Data")
import vworldr as worldBasics
import vplantr as defaultSpecies
import vgraphics as outputGraphics
import list_utils as list_utils
import geometry_utils as geometry_utils

import progressBarClass
###append the path to where species are
sys.path.append("Species")

sList=[]
theCLArgs=""

##########################################
#Import the options#
try:
    theConfig=configparser.RawConfigParser()
    theConfig.optionxform = str 
    theConfig.read('Vida.ini')
    theConfigSection='Vida Options'
except configparser.MissingSectionHeaderError:
    print("Warning: Invalid config file, no [%s] section.") % (theConfigSection)
    raise

theDefaults = {}
converters = [theConfig.getint, theConfig.getboolean, theConfig.getfloat, theConfig.get]
for i in theConfig.items(theConfigSection):
    theItem=i[0]
    for conv in converters:
        try:
            theValue = conv(theConfigSection, theItem)
            if theValue=="None": theValue=None
            break
        except:
            continue
    else:
        print("Unrecognised input value")
    theDefaults[theItem] = theValue
#print theDefaults
#print "#################"

class parseAction(argparse.Action):
    def __call__(self,parser,args,theValues,option_string=None):
        ###reload species option
        if self.dest=="resumeSim":
            theValues=[theValues, True]
        ###video option
        if self.dest=="produceVideo":
            if theValues==None:
                theValues=True
            else:
                try:
                    theValues=[True, int(theValues)]
                except:
                    print("\n***Warning: -v [int] must have an integer value\n   Setting frames per second to the default value")
                    theValues=[True, theDefaults['framesPerSecond']]  
        ###graphical option
        if self.dest=="produceGraphics":
            if theValues==[]:
                theValues=[True, theDefaults['graphicalView']]
            else:
                theValues=[True, theValues]
        ###seed placement option
        if self.dest=="startPopulationSize":
            theOpt=self.option_strings
            if theOpt==['-ss']: theOpt='square'
            elif theOpt==['-sh']: theOpt='hex'
            elif theOpt==['-sf']: theOpt='fromFile'
            else: theOpt='random'
            if theValues==None:
                theValues=[self.default, theOpt]
            else:
                theValues=[theValues, theOpt]
        ###archive options
        if self.dest=="archive" or self.dest=="saveData":
            #theOpt=self.option_strings
            theValues=theValues[0]
        setattr(args, self.dest, theValues)

##############################################

class Species1(defaultSpecies.genericPlant):
    ###The routine in defaultSpecies.genericPlant reads in default values from .yml file
    def __init__(self):
        ##super(type, obj) -> bound super object; requires isinstance(obj, type)
        super(Species1, self).__init__()


def saveSimulationPoint(theDirectory, theFileName, theGarden):
    simulationStateFile =open(theDirectory + theFileName, 'wb')
    pickle.dump(theGarden, simulationStateFile)
    simulationStateFile.close()
    #print "simulation state saved to file"

def saveDataPoint (theDirectory, theFileName, theGarden):
    #Added "Area Canopy" at end of list
    basicHeaders="Cycle #, Plant Name, Species, Mother Plant Name, X Location, Y Location, is a seed, is mature, Age at Maturity, cycles until germination, Age, Mass of Stem, Mass of Canopy, # of Seeds, Mass of all Seeds, Mass Stem+Mass Canopy, Mass Total, Diameter Stem, Radius Canopy, Area covered, Height Stem, Maximum Thickness of a Leaf, Height of Plant, Yearly Growth Stem (kg), Yearly Growth Canopy (kg), Yearly Growth Stem+Canopy (kg), Yearly Growth Stem diameter (m), Yearly Growth Stem Height (m), Average Growth Stem (kg), Average Growth Canopy (kg), Average Growth Stem+Canopy (kg), Average Growth Stem diameter (m), Average Growth Stem Height (m), Cause of Death, Functional Area \n"
    photosynthesisHeaders="leaf is a hemisphere?, area canopy available for photosynthesis, area canopy covered, fraction canopy 100% shaded, canopy transmittance, canopy transmittance impacts photosynthesis?, faction of canopy that needs to be 0% shaded for survival"

    reproductionHeaders="make seeds?, age to start making seeds, height to start making seeds, fraction of mass used for seeds, Maximum Seed Mass, Where seeds grow, Seed dispersal method, fraction of seeds which fail to germinate, delay in germination, fraction of maximum seed mass needed to germinate, fraction of seed mass converted to plant mass"

    allometryHeaders="B1 in Ms=B1*(Mt^a1), a1 in Ms=B1*(Mt^a1), B2 in Mlyoung=B2*(Ms^a2), a2 in Mlyoung=B2*(Ms^a2), B3 in Mlmature=B3*(Ms^a3), a3 in Mlmature=B3*(Ms^a3), B4 in Ds=B4*(Ms^a4), a4 in Ds=B4*(Ms^a4), B5 in Hs=[B5*(Ds^a5)]-B6, a5 in [B5*(Ds^a5)]-B6, B6 in Hs=[B5*(Ds^a5)]-B6, B7 in Mg=[B7*(Ml^a7)]/ area canopy 100% uncovered,  a7 in Mg=[B7*(Ml^a7)]/ area canopy 100% uncovered, B8 in Mpt=B8*(Al^a8), a8 in Mpt=B8*(Al^a8)"


    #theHeader="Plant Name, Mother Plant, Species, X Location, Y Location, Mass Stem, Mass Leaf, # Seeds, Mass all Seeds, Radius Stem, Radius Leaf, Height Plant, Cause of Death \n"
    theHeader= basicHeaders
    thePlantList=[]
    theSeedList=[]
    theCorpseList=[]
    thePlantList.append(theHeader)
    theSeedList.append(theHeader)
    theCorpseList.append(theHeader)
    for plant in theGarden.soil:
        if plant.age>0:
            theData="%i,%s,%s,%s,%f,%f,%s,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s,%f \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlantName,plant.x,plant.y,plant.isSeed,plant.isMature,plant.matureAge,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.areaCovered,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,plant.massStem/plant.age,plant.massLeaf/plant.age,(plant.massStem+plant.massLeaf)/plant.age,(plant.radiusStem*2)/plant.age,plant.heightStem/plant.age,"na",3.14159*plant.radiusLeaf**2-plant.areaCovered)
        else:
            theData="%i,%s,%s,%s,%f,%f,%s,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s,%f \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlantName,plant.x,plant.y,plant.isSeed,plant.isMature,plant.matureAge,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.areaCovered,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,0,0,0,0,0,"na",0)            
        if plant.isSeed:
            theSeedList.append(theData)
        else:
            thePlantList.append(theData)            
    for plant in theGarden.deathNote:
        if plant.age>0:
            theData="%i,%s,%s,%s,%f,%f,%s,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s,%f \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlantName,plant.x,plant.y,plant.isSeed,plant.isMature,plant.matureAge,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.areaCovered,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,plant.massStem/plant.age,plant.massLeaf/plant.age,(plant.massStem+plant.massLeaf)/plant.age,(plant.radiusStem*2)/plant.age,plant.heightStem/plant.age,plant.causeOfDeath,3.14159*plant.radiusLeaf**2-plant.areaCovered)
        else:
            theData="%i,%s,%s,%s,%f,%f,%s,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s,%f \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlantName,plant.x,plant.y,plant.isSeed,plant.isMature,plant.matureAge,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.areaCovered,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,0,0,0,0,0,plant.causeOfDeath,0)
        theCorpseList.append(theData)
    if len(thePlantList)>1:
        saveDataFile =open(theDirectory+"Plants/"+ theFileName, 'w')
        saveDataFile.writelines(thePlantList)
        saveDataFile.close()
    if len(theSeedList)>1:
        saveDataFile =open(theDirectory+"Seeds/"+ theFileName, 'w')
        saveDataFile.writelines(theSeedList)
        saveDataFile.close()
    if len(theCorpseList)>1:
        saveDataFile =open(theDirectory+"Corpses/"+ theFileName, 'w')
        saveDataFile.writelines(theCorpseList)
        saveDataFile.close()
    thePlantList=[]
    theSeedList=[]
    theCorpseList=[]
    #print "simulation data saved to file

    

def makeDirectory(theDirectory):
    if not os.path.exists(theDirectory):
        os.mkdir(theDirectory)
    else:
        ###all this adds an increasing numberic suffix to the folders so
        ###one doesn't overwrite things
        while os.path.exists(theDirectory):
            basicPath=os.path.split(theDirectory)[0]
            i=0
            for n in basicPath:
                i=i-1
                if n=="/": break
                if not basicPath[i].isdigit():break
            theSuffix=""
            if i<-1:
                theSuffix=int(basicPath[i+1:])+1
                basicPath=basicPath[0:i+1]
            else:
                theSuffix=1
            basicPath=basicPath+str(theSuffix)
            theDirectory=basicPath+"/"
        os.mkdir(theDirectory)
    return theDirectory
        
def correctType(theItem):
    returnValue="na"
    if theItem.isdigit():
            returnValue=int(theItem)
    else:
        try:
            returnValue=float(theItem)
        except ValueError:
            try:
                returnValue=str(theItem)
            except ValueError:    
                returnValue="na"
    return returnValue
    
def checkSeedPlacementList(seedPlacementList):
    #remove blank lines that are just \n
    i=0
    for aLine in seedPlacementList:
        if aLine=="\n":seedPlacementList[i]=""
        i=i+1
    i=0
    for aLine in seedPlacementList:
        if not aLine=="":
            aLine=aLine.rstrip("\n")
            aLine=aLine.split(",")
            for j in range(len(aLine)):
                if not j==0: aLine[j]=aLine[j].strip()
            theLength=len(aLine)
            if theLength>5: del aLine[5:theLength] #if it is too long, just chop it
            #if too short, make it longer
            if theLength<5:
                toAdd=5-theLength
                for k in range(toAdd):
                    aLine.append("0.0")
            aLine= map(correctType, aLine)
            seedPlacementList[i]=aLine
        i=i+1
    i=0
    printErrorMessage=0
    for aLine in seedPlacementList:
        if aLine=="":
            del seedPlacementList[i]
            i=i+1
        elif not type(aLine[0])==str or not type(aLine[1])==float or not type(aLine[2])==float or not type(aLine[3])==int or not type(aLine[4])==float:
            printErrorMessage=1
            del seedPlacementList[i]
            i=i+1
    if printErrorMessage:
        print("***Improper seeding file format...")
        print("     Questionable lines will be ignored.")
    return seedPlacementList
            

def correctSList(sList):
    startPopulationSize=thePrefs.startPopulationSize
    ###this is probably a list###
    sList=sList[1:-1]
    sList=sList.split(",")
    sList=map(correctType, sList)
    i=0
    showSAlert1=0
    showSAlert2=0
    showSAlert3=0
    for x in sList:
        if i==0 and type(x)==int:
            #the first item is a number. This is not correct
            #insert the default species here
            showSAlert1=1
            showSAlert2=1
            sList.insert(0, "_random_")
        if i+1==len(sList) and type(sList[i])==str:
            #the last item in the list is a string
            #put a int after it
            showSAlert1=1
            showSAlert3=1
            sList.insert(i+1, thePrefs.startPopulationSize)
        elif type(sList[i])==str and type(sList[i+1])==str:
            #this is probably a two species names next to one another
            #insert a int between them
            showSAlert1=1
            showSAlert3=1
            sList.insert(i+1, thePrefs.startPopulationSize)
        elif type(sList[i])==int and type(sList[i-1])==int:
            showSAlert1=1
            showSAlert2=1
            sList.insert(i, "_random_")
        i=i+1
    if showSAlert1: print("***Improper seeding [list] format...")
    if showSAlert2: print("     Inserting random species...")
    if showSAlert3: print("     Inserting default starting population size...")
    if showSAlert1: print("        input set to: %s." % (sList))
    return sList
    
def main():
    #why do only these need to be reminded they are global?
    global simulationFile
    global theWorldSize
    global startPopulationSize
    global seedPlacement
    global sList
    global theCLArgs
    
    print("*********Vida version: %s *********" % (vidaVersion))

    CFDGtext=""
    CFDGtextDict={}
    
    ####################################
    ###experiments in importing events
    import yaml
        #if eventFile!=None and os.path.exists(eventFile):
    if eventFile!=None:
        #if type(eventFile)==file:
        print("***Loading event file: %s***" % (eventFile.name))
        #theFile=open(eventFile)
        #eventData=yaml.load(theFile)
        eventData=yaml.load(eventFile)
        #theFile.close
        eventTimes=eventData.keys()
    else:
        eventTimes=[]
    #####################################
    
    if debug==1: print("***debug is on***")

    theGarden= worldBasics.garden()
    theGarden.platonicSeeds={}
    theGarden.theRegions=[]

    
    ####

    #########Check for multiple species. If none, use default
    fileList=os.listdir("Species")
    ymlList=[]
    pythonList=[]
    useDefaultYml=True
    print("***Checking for species...***")
    for file in fileList:
        theExtension=os.path.splitext(file)[1]
        if theExtension==".yml":
            #add this file to the list of yaml files
            ymlList.append(file)
            useDefaultYml=False
        elif theExtension==".py":
            #this might be override info for a species
            #add this file to the list of species python files
            #this isn't implemented
            pythonList.append(file)
    fileList=[]
    ##########

    if resumeSim==True and not simulationFile=="":
        print("***Loading simulation: %s...***" % (simulationFile.name))
        #simulationFile=open(simulationFile, 'r')
        theGarden=pickle.load(simulationFile)
        #simulationFile.close()
        theWorldSize=theGarden.theWorldSize
        print("***Resuming Simulation: %s as %s***" % (theGarden.name, simulationName))
        theGarden.name=simulationName
        startPopulationSize=theGarden.numbPlants
        ##this should reload species data.
        ###Important if you want to compare runs
        if reloadSpeciesData==True:
            print("***Reloading species data...***")
            ###fileLoc will be different for each species eventually
            fileLoc="Vida_Data/Default_species.yml"
            for item in theGarden.soil:
                item.importPrefs(fileLoc)
    else:
        theGarden.makePlatonicSeedDict(ymlList, Species1)
        print("***Species loaded.***")
        theGarden.name=simulationName
        theGarden.theWorldSize=theWorldSize
        print("***Beginning Simulation: %s***" % (simulationName))

    theGarden.showProgressBar=showProgressBar

    print("     World size: %ix%i" % (theWorldSize, theWorldSize))
    print("     Maximum population size will be: %i" % (maxPopulation))
    print("              and")
    print("     Running simulation for %i cycles" % (maxCycles))
    print("              (whichever comes first)")
    print("     Starting population size: %i" % (startPopulationSize))
    if theGarden.carbonAllocationMethod==0:
        print("     Plants will allocate carbon to stem and leaf using methods defined by the species.")
    else:
        print("     All plants will allocate carbon to stem and leaf using method %i" % (theGarden.carbonAllocationMethod))

    print("")
    if produceGraphics==True: 
        print("     Graphical output will be produced.")
        for aView in graphicalView:
            if aView=="3d":
                print("       Graphical output will be 3d.")
            if aView==1:
                print("       Graphical output will be a bottom-up view.")
            if aView==2:
                print("       Graphical output will be a top-down view.")
            if aView==3:
                print("       Graphical output will be a side-view.")
            if aView==12:
                print("       Graphical output will be a combination bottom-up and top-down view.")
            if aView==21:
                print("       Graphical output will be a combination top-down and bottom-up view.")
            if aView==13 or aView==31:
                print("       Graphical output will be a combined top-down and side view.")
            if aView==23:
                print("       Graphical output will be a combined bottom-up and side view.")
            if aView==123:
                print("       Graphical output will be a combination bottom-up, top-down and side view.")
        if produceVideo==True:
            print("       Graphical output will include a %s frame/second video." % (framesPerSecond))
    ###I think this is where to start the times to repeat bit
    for x in range(timesToRepeat):
        ###make necessary directories
        outputDirectory="Output-"+simulationName+"/"
        outputDirectory=makeDirectory(outputDirectory)
        ###save the command line arguments
        theCLArgs=" ".join(map(str, theCLArgs))
        theCLIfile=open(outputDirectory+"CLI_arguments.txt", 'w')
        theCLIfile.writelines(theCLArgs)
        theCLIfile.close()
        #if produceGraphics==1 or produceDXFGraphics==1:
        if produceGraphics==True:
            baseGraphicsDirectory = outputDirectory +"Graphics/"
            makeDirectory(baseGraphicsDirectory)
            outputGraphicsDirectoryDict={}
            for aView in graphicalView:
                if aView=='3d':
                    outputGraphicsDirectory = baseGraphicsDirectory +"DXF/"
                if aView==1:
                    outputGraphicsDirectory = baseGraphicsDirectory +"bottom-up/"
                if aView==2:
                    outputGraphicsDirectory = baseGraphicsDirectory +"top-down/"
                if aView==3:
                    outputGraphicsDirectory = baseGraphicsDirectory +"side/"
                if aView==12:
                    outputGraphicsDirectory = baseGraphicsDirectory +"combined-bottom-top/"
                if aView==21:
                    outputGraphicsDirectory = baseGraphicsDirectory +"combined-top-bottom/"
                if aView==13 or aView==31:
                    outputGraphicsDirectory = baseGraphicsDirectory +"combined-bottom-side/"
                if aView==23:
                    outputGraphicsDirectory = baseGraphicsDirectory +"combined-top-side/"
                if aView==123:
                    outputGraphicsDirectory = baseGraphicsDirectory +"combined-bottom-top-side/"
                outputGraphicsDirectoryDict[aView]=outputGraphicsDirectory
                makeDirectory(outputGraphicsDirectory)
        if not archive=="n":
            saveDirectory = outputDirectory+"Save_points/"
            makeDirectory(saveDirectory)
        if not saveData=="n":
            dataDirectory = outputDirectory+"Simulation_data/"
            makeDirectory(dataDirectory)
            makeDirectory(dataDirectory+"Seeds/")
            makeDirectory(dataDirectory+"Plants/")
            makeDirectory(dataDirectory+"Corpses/")


        
        if resumeSim==None:
            #2008.11.06 Moved a huge block of code related to placing seeds to vworldr.py
            theGarden.placeSeed(seedPlacement, sList, startPopulationSize, useDefaultYml, ymlList)
        if produceGraphics==True and CFDGtextDict=={}:
            for aView in graphicalView:
                if aView!="3d":
                    #print aView
                    CFDGtextDict[aView]=outputGraphics.initCFDGText(theGarden, aView, percentTimeStamp, 50.0)
#print CFDGtextDict
        #######
        cycleNumber=0
        print("\n***Running simulation.***")
        if not showProgressBar:
            theProgressBar= progressBarClass.progressbarClass(maxCycles,"*") #why -1? because index 0. So if total=100, 0-99.
        while (theGarden.numbPlants<=maxPopulation and cycleNumber<=maxCycles) and (theGarden.numbPlants+theGarden.numbSeeds)>0:
            ###################################################################################
            ####Experimental scripting event stuff                                            #
            if cycleNumber in eventTimes:                                                     # 
                for aItem in eventData[cycleNumber]:                                          #
                    for aKey in aItem.keys():                                                 #
                        if aKey=="Garden":                                                    #
                            if debug==1: print("debug: A garden related event has been triggered.")
                            theDict=aItem[aKey][0]                                            #
                            gardenAttrs=theDict.keys()                                        #
                            for theGardenAttr in gardenAttrs:                                 #
                                setattr(theGarden, theGardenAttr, theDict[theGardenAttr])     #
                            gardenAttrs=""    
                        elif aKey=="Killzone" or aKey=="Safezone":
                            if debug==1: print("debug: generation of a zone event has been triggered.")
                            theDict=aItem[aKey][0]                                           #
                            zoneAttrs=theDict.keys()
                            zoneX=float(theDict['x'])
                            zoneY=float(theDict['y'])
                            zoneSize=float(theDict['size'])
                            zoneShape=theDict['shape']
                            zoneTarget=theDict['target']
                            if 'species' in theDict:
                                zoneSpecies=theDict['species']
                            else:
                                zoneSpecies = 'all'
                            if zoneShape not in ['circle','square']:
                                print("***WARNING: improper zone shape defined. Defaulting to square.***")
                                zoneShape='square'
                            zoneTarget=theDict['target']
                            if zoneTarget not in ['all','plants','seeds']:
                                print("***WARNING: improper zone target defined. Defaulting to all.***")
                                zoneTarget='all'

                            killThese=[]
                            if zoneShape=='circle':
                                for theObject in theGarden.soil:
                                    if theObject.isSeed:
                                        r=theObject.radiusSeed
                                    else:
                                        r=theObject.radiusStem
                                    theResult=geometry_utils.checkOverlap(theObject.x, theObject.y, r, zoneX, zoneY, zoneSize)
                                    if theResult>0 and aKey=='Killzone':
                                        if (zoneSpecies == 'all') or (theObject.nameSpecies == zoneSpecies):                                            
                                            if zoneTarget=='all' or (theObject.isSeed and zoneTarget=='seeds') or (not theObject.isSeed and zoneTarget=='plants'):
                                                killThese.append(theObject)   
                                    elif aKey=='Safezone':
                                        if theResult==0:
                                            killThese.append(theObject)
                                        elif theResult>0:
                                            if (theObject.isSeed and zoneTarget=='plants') or (not theObject.isSeed and zoneTarget=='seeds'):
                                                killThese.append(theObject)    
                                                                                
                            else:
                                for theObject in theGarden.soil:
                                    objectX=theObject.x
                                    objectY=theObject.y
                                    theResult=geometry_utils.pointInsideSquare(zoneX, zoneY, zoneSize, objectX, objectY)
                                    if theResult>0 and aKey=='Killzone':
                                        if (zoneSpecies == 'all') or (theObject.nameSpecies == zoneSpecies):                                      
                                            if zoneTarget=='all' or (theObject.isSeed and zoneTarget=='seeds') or (not theObject.isSeed and zoneTarget=='plants'):
                                                killThese.append(theObject) 
                                    elif aKey=='Safezone':
                                        if theResult==0:
                                            killThese.append(theObject)
                                        elif theResult>0:
                                            if (theObject.isSeed and zoneTarget=='plants') or (not theObject.isSeed and zoneTarget=='seeds'):
                                                killThese.append(theObject)  

                            for theObject in killThese:
                                theObject.causeOfDeath="zone"
                                theGarden.kill(theObject)



                        elif aKey=="Seed":
                            if debug==1: print("debug: A seeding related event has been triggered.")   #
                            theDict=aItem[aKey][0]                                            #
                            seedingInfo=theDict.keys()                                        #
                            for infoItem in seedingInfo:
                                if infoItem=="number" and not seedPlacement=="fromFile": startPopulationSize=theDict[infoItem]
                                if infoItem=="species": 
                                    sList=theDict[infoItem]
                                    if sList=="random": sList=[]
                                if infoItem=="placement": seedPlacement=theDict[infoItem]
                                if seedPlacement=="hexagon": seedPlacement="hex" #just make sure it is consistant
                                if os.path.isfile(seedPlacement):
                                    if debug == 1: print("debug: Confirming placement file exists....")
                                    theFile=open(seedPlacement)
                                    try:
                                        sList=theFile.readlines()
                                    finally:
                                        theFile.close()
                                    sList=checkSeedPlacementList(sList)
                                    startPopulationSize=len(sList)
                                    seedPlacement="fromFile"
                                    if debug ==1: print("debug: Will place seeds from a file")
                                    ###if a simulation is being reloaded from a pickle, that sim might not have saved
                                    ###data on a new species being introduced. Load the new species and add it to the platonic list
                                    ###so it can be added to theGarden
                                    for j in sList:
                                        jj=j[0]
                                        if not theGarden.platonicSeeds.has_key(jj):
                                            if debug == 1: print("debug: Desired species missing from loaded simulation")
                                            if debug == 1: print("debug: Adding species %s" % (jj))
                                            theSeed=Species1()
                                            fileLoc= "Species/"+jj
                                            theSeed.importPrefs(fileLoc)
                                            theSeed.name="Platonic %s" % jj
                                            theGarden.platonicSeeds[jj]=theSeed



                            if not seedPlacement=="fromFile" and not sList==[]:
                                newList=[]
                                for j in range(startPopulationSize):
                                    newList.append(sList)
                                ###if a simulation is being reloaded from a pickle, that sim might not have saved
                                ###data on a new species being introduced. Load the new species and add it to the platonic list
                                ###so it can be added to theGarden
                                sList=newList
                                newList=list(set(sList))
                                for j in newList:
                                    if not theGarden.platonicSeeds.has_key(j):
                                        #print "adding %s" % (j)
                                        theSeed=Species1()
                                        fileLoc= "Species/"+j
                                        theSeed.importPrefs(fileLoc)
                                        theSeed.name="Platonic %s" % j
                                        theGarden.platonicSeeds[j]=theSeed

                            theGarden.placeSeed(seedPlacement, sList, startPopulationSize, useDefaultYml, ymlList)
                        elif aKey=="Region":
                            if debug: print("debug: Region event detected...")
                            theDict=aItem[aKey][0] 
                            regionAttrs=theDict.keys()
                            theRegionName=str(theDict['name'])
                            if debug: print("debug: Region %s event detected." % (theRegionName))
                            regionNames=[]
                            for i in theGarden.theRegions:
                                regionNames.append(i.name)
                            if theRegionName in regionNames:
                                for j in theGarden.theRegions:
                                    if j.name==theRegionName:
                                        theRegion=j
                                        break
                                for aAttr in regionAttrs:
                                    if not getattr(theRegion,aAttr,"does not exist")==theDict[aAttr]:
                                        if debug: print("debug: Region %s has had a change in one or more attributes." % (theRegionName))
                                        updatePlants=True
                                        break
                                #if (not theRegion.size==theDict["size"]) or (not theRegion.x==theDict["x"]) or (not theRegion.y==theDict["y"]) or (not theRegion.shape==theDict["shape"]):
                                #    if debug:print "debug: a region has changed shape, size or location"
                                #    updatePlants=True
                                ##now just read in the values#
                                if debug: print("debug: Updating attributes for region %s." % (theRegionName))
                                for theRegionAttr in regionAttrs:                                 #
                                    setattr(theRegion, theRegionAttr, theDict[theRegionAttr])     #
                                if updatePlants:
                                    if debug:print("debug: updating plants with changed region info")
                                    for aPlant in theGarden.soil:
                                        plantX=aPlant.x
                                        plantY=aPlant.y
                                        if theRegion.shape=='square':
                                            inSubregion=geometry_utils.pointInsideSquare(theRegion.x, theRegion.y, theRegion.size, plantX, plantY)
                                        elif theRegion.shape=='circle':
                                            #size needs to be radius but region defines diameter
                                            inSubregion=geometry_utils.pointInsideCircle(theRegion.x, theRegion.y, theRegion.size/2.0, plantX, plantY)
                                        if inSubregion:
                                            if not theRegion in aPlant.subregion:
                                                aPlant.subregion.append(theRegion)
                                                #print "\nX: %f  Y: %f  In region: %s" % (plantX, plantY, newRegion)

                                #print theRegion.size
                            else:
                                newRegion=worldBasics.garden()
                                newRegion.name=theRegionName
                                ###these are default values###
                                newRegion.x=0.0              #
                                newRegion.y=0.0              #
                                newRegion.worldSize=1.0      #
                                newRegion.shape='square'     #
                                ##############################
                                ##now just read in the values#
                                if debug: print("debug: Making attributes for region")
                                for theRegionAttr in regionAttrs:                                 #
                                    setattr(newRegion, theRegionAttr, theDict[theRegionAttr])     #
                                theGarden.theRegions.append(newRegion)
                                for aPlant in theGarden.soil:
                                    plantX=aPlant.x
                                    plantY=aPlant.y
                                    if newRegion.shape=='square':
                                        inSubregion=geometry_utils.pointInsideSquare(newRegion.x, newRegion.y, newRegion.size, plantX, plantY)
                                    elif newRegion.shape=='circle':
                                        #size needs to be radius but region defines diameter
                                        inSubregion=geometry_utils.pointInsideCircle(newRegion.x, newRegion.y, newRegion.size/2.0, plantX, plantY)
                                    if inSubregion:
                                        if not newRegion in aPlant.subregion:
                                            aPlant.subregion.append(newRegion)
                                            #print "\nX: %f  Y: %f  In region: %s" % (plantX, plantY, newRegion)
                                        
                                newRegion=""
                            
                            
                        theDict=[]#just clear this to free up the memory
            ###################################################################################
            theGarden.cycleNumber=cycleNumber
            if not showProgressBar:
                    theProgressBar.update(cycleNumber)

            ###START OF SEEING CHANGES TO SPECIES FOLDER
            #########Check for multiple species. If none, use default
            fileList=os.listdir("Species")
            #print fileList
            #ymlList=[]
            #print "***Checking for species...***"
            #for file in fileList:
            #    theExtension=os.path.splitext(file)[1]
            #    if theExtension==".yml":
            #        #add this file to the list of yaml files
            #        ymlList.append(file)
            #        useDefaultYml=False
            #fileList=[]
            ##########





            if debug==1: print("number of plants: "+str(theGarden.numbPlants))
            if debug==1: print("number of seeds: "+str(theGarden.numbSeeds))
            
            #generate graphics if requested
            if produceGraphics==True:
                theView=list(graphicalView)#copy graphicalView list to theView
                if "3d" in graphicalView:
                    theIndex=theView.index("3d")
                    theView.pop(theIndex)
                    theData=vdxfGraphics.makeDXF(theGarden)
                    theFileName= simulationName+str(cycleNumber)
                    vdxfGraphics.writeDXF(outputGraphicsDirectoryDict["3d"], theFileName, theData)
                if len(theView)!=0:
                    for aView in theView:
                        theData=outputGraphics.makeCFDG(aView, CFDGtextDict[aView], theGarden, cycleNumber)
                        if aView==1:
                            cfdgFileName= simulationName +"-bottom-"+str(cycleNumber)
                        elif aView==2:
                            cfdgFileName= simulationName +"-top-"+str(cycleNumber)
                        elif aView==3:
                            cfdgFileName= simulationName +"-side-"+str(cycleNumber)
                        elif aView==12:
                            cfdgFileName= simulationName +"-bottom-top-"+str(cycleNumber)
                        elif aView==21:
                            cfdgFileName= simulationName +"-top-bottom-"+str(cycleNumber)
                        elif aView==13 or aView==31:
                            cfdgFileName= simulationName +"-bottom-side-"+str(cycleNumber)
                        elif aView==23 or aView==32:
                            cfdgFileName= simulationName +"-top-side-"+str(cycleNumber)
                        elif aView==123:
                            cfdgFileName= simulationName +"-bottom-top-side"+str(cycleNumber)
                        #outputGraphics.writeCFDG(outputGraphicsDirectory, cfdgFileName, theData)
                        outputGraphics.writeCFDG(outputGraphicsDirectoryDict[aView], cfdgFileName, theData)

            ###go through the soil list and germinate seed or grow plant
            if theGarden.showProgressBar:
                print("***Allowing plants a turn to grow***")
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                theBar=0
            for obj in theGarden.soil[:]:
                if obj.isSeed:
                    obj.germinate(theGarden)
                else:
                    obj.growPlant(theGarden)
                if theGarden.showProgressBar:
                    theBar=theBar+1
                    theProgressBar.update(theBar)

            ###deal with violaters of basic physics
            theGarden.causeRandomDeath()
            theGarden.checkSenescence()
            theGarden.checkDistanceMortality()
            theGarden.removeOffWorldViolaters()
            theGarden.removeEulerGreenhillViolaters()
            theGarden.removeOverlaps()
            
            ###sort the garden.soil by height of the plants.Ordered shortest to tallest
            theGarden.soil= list_utils.sort_by_attr(theGarden.soil, "heightStem")
            ###flip the list so it's ordered tallest to shortest
            theGarden.soil.reverse()

            ###work out shading
            worldBasics.determineShade(theGarden)

            ###Calculate the amount of carbon each plant will have to start the next turn
            if theGarden.showProgressBar:
                print("***Calculating new mass from photosynthesis***")
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                i=0
            for plant in theGarden.soil[:]:
                if plant.isSeed==False:
                    plant.massFixed=plant.calcNewMassFromLeaf(theGarden)
                    if plant.massFixed==-1.0:
                        plant.causeOfDeath="lack of light"
                        theGarden.kill(plant)
                    else:
                        plant.massFixedRecord.append(plant.massFixed)
                        while len(plant.massFixedRecord)>plant.numYearsGrowthMemory:
                            plant.massFixedRecord.pop(0)
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)

            if archive=="a" or (archive=="s" and cycleNumber==0):
                fileName=simulationName+'-'+str(cycleNumber)+'.pickle'
                saveSimulationPoint(saveDirectory, fileName, theGarden)
            if saveData=="a" or (saveData=="s" and cycleNumber==0):
                fileName=simulationName+'-'+str(cycleNumber)+'.csv'
                saveDataPoint(dataDirectory, fileName, theGarden)

            #print theGarden.deathNote
            theGarden.deathNote=[]        
            
            cycleNumber= cycleNumber+1

        if archive=="e":
            fileName=simulationName+'-'+str(cycleNumber)+'.pickle'
            saveSimulationPoint(saveDirectory, fileName, theGarden)
        if saveData=="e":
                fileName=simulationName+'-'+str(cycleNumber)+'.csv'
                saveDataPoint(dataDirectory, fileName, theGarden)
                
                            
#if produceStats:
        if saveData=="a":
            ###the real solution is to refaction vextract so it can be
            ###command line OR imported
            if "PyPy" in sys.version:
                theRunEnv="pypy"
            else:
                theRunEnv="python"
            theArgument="-n '%s' -fs" % (dataDirectory+"Seeds/")
            print("\n***sending to Extract: %s" % (theArgument))
            os.system("%s Vida_Data/vextract.py %s" % (theRunEnv, theArgument))
            theArgument="-n '%s' -fs" % (dataDirectory+"Plants/")
            print("***sending to Extract: %s" % (theArgument))
            os.system("%s Vida_Data/vextract.py %s" % (theRunEnv, theArgument))
            theArgument="-n '%s' -fs" % (dataDirectory+"Corpses/")
            print("***sending to Extract: %s" % (theArgument))
            os.system("%s Vida_Data/vextract.py %s" % (theRunEnv, theArgument))


        ###final graphics calls
        if produceGraphics==True:
             for aView in graphicalView:
                if aView!="3d":
                    print("\nProducing PNG files...")
                    #print outputGraphicsDirectoryDict[aView]
                    outputGraphics.outputPNGs(outputGraphicsDirectoryDict[aView], outputGraphicsDirectoryDict[aView])
                    if deleteCfdgFiles==True:
                        print("Deleting .cfdg files...")
                        outputGraphics.deleteCFDGFiles(outputGraphicsDirectoryDict[aView])

        ###only try and make a video if it is wanted and if pngs were made
        if produceVideo==True and produceGraphics==True:
            print("Producing video file..." )
            for aView in graphicalView:
                if aView!="3d":
                    outputGraphics.outputMOV(outputGraphicsDirectoryDict[aView], simulationName, framesPerSecond)
                    time.sleep(1)
        print("\n*****Simulation Complete*****")
        #clear the values
        theGarden.soil=[]
        theGarden.deathNote=[]
        theGarden.cycleNumber=0
        for aRegion in theGarden.theRegions:
            aRegion.size=0.0
        #print theGarden.theRegions[0].size
    ###And this would be the end of the loop bit

        
                
if __name__ == '__main__':
    theCLArgs=sys.argv
    ###Argument parsing
    parser=argparse.ArgumentParser(description='blargity blarg blarg')
    parser.add_argument('-n', type=str, metavar='string', dest='simulationName', required=False, help='Name of the simulation')
    parser.add_argument('-w', type=int, metavar='int', dest='theWorldSize', required=False, help='Size of the world')
    parser.add_argument('-x', type=int, metavar='int', dest='timesToRepeat', required=False, help='Times to repeat simulation')
    parser.add_argument('-m', type=int, metavar='int', dest='maxPopulation', required=False, help='Maximum population before stop')
    parser.add_argument('-t', type=int, metavar='int', dest='maxCycles', required=False, help='Maximum time before stop')
    parser.add_argument('-i', type=float, metavar='float', dest='percentTimeStamp', required=False, help='Percent size of time stamp')
    parser.add_argument('-d', dest='debug', action='store_true', required=False, help='Debug level 1')
    parser.add_argument('-dd',dest='debug2',action='store_true', required=False, help='Debug level 2')
    parser.add_argument('-c', dest='deleteCfdgFiles', action='store_false', required=False, help='Keep cfdg files')
    parser.add_argument('-p', dest='deletePngFiles', action='store_true', required=False, help='Delete png files')
    parser.add_argument('-b', dest='showProgressBar', action='store_true', required=False, help='Show progress bars')    
    parser.add_argument('-r', metavar='file', type=argparse.FileType('r'), dest='resumeSim', required=False, help='Load a saved simulation and continue')
    parser.add_argument('-e', metavar='file', type=argparse.FileType('r'), dest='eventFile', required=False, help='Load an event file')    
    ###options that use a code action
    parser.add_argument('-rl', metavar='file', type=argparse.FileType('r'), dest='resumeSim', action=parseAction, required=False, help='NOT FULLY IMPLEMENTED')
    parser.add_argument('-v', type=int, metavar='int', nargs='?', action=parseAction, dest='produceVideo', required=False, help='Produce a video from images. Optional frames/second')    
    parser.add_argument('-g', nargs='*', type=str, action=parseAction, dest='produceGraphics', required=False, choices=['b','t','s','ts','st','bs','sb','bt','tb','bts','3d' ], help='Graphical view desired')    
    parser.add_argument('-s', type=int, metavar='int', nargs='?', dest='startPopulationSize', action=parseAction)
    parser.add_argument('-ss', type=int, metavar='int', nargs='?', dest='startPopulationSize', action=parseAction)
    parser.add_argument('-sh', type=int, metavar='int', nargs='?', dest='startPopulationSize', action=parseAction)
    parser.add_argument('-sf', type=argparse.FileType('r'), metavar='file', dest='startPopulationSize', action=parseAction)
    ###slighly overloaded options
    parser.add_argument('-a', type=str, dest='archive', action=parseAction, nargs=1, choices=['a', 'e','n','s'])
    parser.add_argument('-ai', type=str, dest='archive', action=parseAction, nargs=1 )
    parser.add_argument('-f', type=str, dest='saveData', action=parseAction, nargs=1, choices=['a', 'e','n','s'])
    parser.add_argument('-fi', type=str, dest='saveData', action=parseAction, nargs=1 )
    
    ##########
    
    parser.set_defaults(**theDefaults)
    
    theOptsVals=vars(parser.parse_args())#have it presented as a dict
    theOpts=theOptsVals.keys()#this returns a list of the arguments entered
    
    globalVarsVals=globals()#dictionary of all local variables and their values
    
    for theVar in theOpts:
        globalVarsVals[theVar]=theOptsVals[theVar]
    
    ###parse the graphic options a bit more
    if type(produceGraphics)==list:
        graphicalView=produceGraphics[1]
        if "3d" in graphicalView:
            import vdxfGraphics
        produceGraphics=produceGraphics[0]    
    if type(graphicalView)!=list:
        graphicalView=[graphicalView]#make sure the graphicalView is a list
    #now convert the letter code into the number code used
    for i in range(len(graphicalView)):
        if graphicalView[i]!='3d':
            graphicalView[i]=graphicalView[i].replace('b','1')
            graphicalView[i]=graphicalView[i].replace('t','2')
            graphicalView[i]=graphicalView[i].replace('s','3')
            graphicalView[i]=graphicalView[i].replace('21','12')
            graphicalView[i]=graphicalView[i].replace('31','13')
            graphicalView[i]=graphicalView[i].replace('32','23')
            graphicalView[i]=int(graphicalView[i])
    graphicalView=list_utils.remove_duplicates(graphicalView)
    
    ###parse the video options a bit more
    if type(produceVideo)==list:
        framesPerSecond=produceVideo[1]
        produceVideo=produceVideo[0]
    if produceVideo==True:
        if produceGraphics==False:
            print("***Warning: A video output was desired, but a graphical option was not specified\n   Graphical output has been set to the default")
            produceGraphics=True
            graphicalView=[theDefaults['graphicalView']]
        if graphicalView==['3d']:
            print("***Warning: A video can not be auto generated from the '3d' graphical option\n   Video output turned off")
            produceVideo=False
    ##parse resume sim option a bit more
    if type(resumeSim)==argparse.FileType('r'):
        simulationFile=resumeSim
        resumeSim=True
        reloadSpeciesData=False
    elif type(resumeSim)==list:
        simulationFile=resumeSim[0]
        reloadSpeciesData=resumeSim[1]
        resumeSim=True
    ###parse seed placement options a bit more
    if type(startPopulationSize)==list:
        seedPlacement=startPopulationSize[1]
        startPopulationSize=startPopulationSize[0]
    if type(startPopulationSize)==argparse.FileType('r'):
        sList=startPopulationSize.readlines()
        ##send the file off to make sure it's in the correct format
        sList=checkSeedPlacementList(sList)
        startPopulationSize=len(sList)
    
    
    
        #for x in theOpts:
#print "%s: \t%s   %s" % (x, theDefaults[x], globalVarsVals[x])
    
    theDefaults=None#just clear it to free up memory


    main()
else:
    main()

    
    


        

