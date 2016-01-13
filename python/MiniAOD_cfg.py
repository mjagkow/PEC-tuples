""" This module defines a general configuration for analyses involving t-channel single top-quark
    production. It performs a very loose event selection (at least one semi-tight lepton, at least
    two jet with pt > 30 GeV/c). Necessary event cleaning (mostly recommended for MET analyses) is
    applied and quality cuts for different physical objects are defined. Corrected MET as well as
    all the corresponding systematics are calculated. Isolation requirements for charged leptons are
    dropped (they are applied only for jet clustering and MET systematics due to lepton energy
    scale).
    
    The results are saved with the help of dedicated EDAnalyzer's. No EDM output is produced.
    
    The workflow can be controlled through the VarParsing options defined in the code below.
    """

import sys
import random
import string
import re


# Create a process
import FWCore.ParameterSet.Config as cms
process = cms.Process('Analysis')


# Enable MessageLogger
process.load('FWCore.MessageLogger.MessageLogger_cfi')

# Reduce verbosity
process.MessageLogger.cerr.FwkReport.reportEvery = 100


# Ask to print a summary in the log
process.options = cms.untracked.PSet(
    wantSummary = cms.untracked.bool(True),
    allowUnscheduled = cms.untracked.bool(True))


# Parse command-line options
from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('python')

options.register('runOnData', False, VarParsing.multiplicity.singleton,
    VarParsing.varType.bool, 'Indicates whether it runs on the real data')
options.register('isPromptReco', False, VarParsing.multiplicity.singleton,
    VarParsing.varType.bool,
    'In case of data, distinguishes PromptReco and ReReco. Ignored for simulation')
options.register('saveLHEWeightVars', True, VarParsing.multiplicity.singleton,
    VarParsing.varType.bool,
    'Indicates whether LHE-level variations of event weights should be stored')
options.register('globalTag', '', VarParsing.multiplicity.singleton,
    VarParsing.varType.string, 'The relevant global tag')
# The outputName is postfixed with ".root" automatically
options.register('outputName', 'sample', VarParsing.multiplicity.singleton,
    VarParsing.varType.string, 'The name of the output ROOT file')
# The leptonic channels to be processed. 'e' stands for electron, 'm' -- for muon
options.register('channels', 'em', VarParsing.multiplicity.singleton, VarParsing.varType.string,
    'The leptonic channels to process')
options.register('saveGenParticles', False, VarParsing.multiplicity.singleton,
    VarParsing.varType.bool,
    'Save information about the hard(est) interaction and selected particles')
options.register('saveHeavyFlavours', False, VarParsing.multiplicity.singleton,
    VarParsing.varType.bool, 'Saves information about heavy-flavour quarks in parton shower')
options.register('saveGenJets', False, VarParsing.multiplicity.singleton, VarParsing.varType.bool,
    'Save information about generator-level jets')
options.register('inputFile', '', VarParsing.multiplicity.singleton, VarParsing.varType.string,
    'The name of the source file')
options.register('runOnFastSim', False, VarParsing.multiplicity.singleton,
    VarParsing.varType.bool, 'Indicates whether FastSim is processed')
options.register('jetSel', '2j30', VarParsing.multiplicity.singleton, VarParsing.varType.string,
    'Selection on jets. E.g. 2j30 means that an event must contain at least 2 jets with '
    'pt > 30 GeV/c')

options.parseArguments()


# Make the shortcuts to access some of the configuration options easily
runOnData = options.runOnData
elChan = (options.channels.find('e') != -1)
muChan = (options.channels.find('m') != -1)


# Provide a default global tag if user has not given any. It is set as recommended for JEC
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/JECDataMC?rev=98
if len(options.globalTag) == 0:
    if runOnData:
        options.globalTag = '74X_dataRun2_v5'
    else:
        options.globalTag = '74X_mcRun2_asymptotic_v4'
    
    print 'WARNING: No global tag provided. Will use the default one (' + options.globalTag + ')'

# Set the global tag
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
from Configuration.AlCa.GlobalTag_condDBv2 import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, options.globalTag)


# Parse jet selection
jetSelParsed = re.match(r'(\d+)j(\d+)', options.jetSel)
if jetSelParsed is None:
    print 'Cannot parse jet selection "' + options.jetSel + '". Aborted.'
    sys.exit(1)
 
minNumJets = int(jetSelParsed.group(1))
jetPtThreshold = int(jetSelParsed.group(2))
print 'Will select events with at least', minNumJets, 'jets with pt >', jetPtThreshold, 'GeV/c.'


# Define the input files
process.source = cms.Source('PoolSource')

if len(options.inputFile) > 0:
    process.source.fileNames = cms.untracked.vstring(options.inputFile)
else:
    # Default input files for testing
    if runOnData:
        # from PhysicsTools.PatAlgos.patInputFiles_cff import filesRelValSingleMuMINIAOD
        # process.source.fileNames = filesRelValSingleMuMINIAOD
        process.source.fileNames = cms.untracked.vstring('/store/data/Run2015D/SingleMuon/MINIAOD/PromptReco-v4/000/258/159/00000/6CA1C627-246C-E511-8A6A-02163E014147.root')
        options.isPromptReco = True
    else:
        # from PhysicsTools.PatAlgos.patInputFiles_cff import filesRelValTTbarPileUpMINIAODSIM
        # process.source.fileNames = filesRelValTTbarPileUpMINIAODSIM
        process.source.fileNames = cms.untracked.vstring('/store/mc/RunIISpring15MiniAODv2/TT_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/74X_mcRun2_asymptotic_v2-v1/40000/00087FEB-236E-E511-9ACB-003048FF86CA.root')

# process.source.fileNames = cms.untracked.vstring('/store/relval/...')

# Set a specific event range here (useful for debugging)
# process.source.eventsToProcess = cms.untracked.VEventRange('1:5')

# Set the maximum number of events to process for a local run (it is overiden by CRAB)
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(100))


# Define the paths. There is one path per each channel (electron or muon).
# Note that every module is guarenteed to run only once per event despite it can be included
# into several paths
process.elPath = cms.Path()
process.muPath = cms.Path()

# Make a simple class to add modules to all the paths simultaneously
class PathManager:
    def __init__(self, *paths_):
        self.paths = []
        for p in paths_:
            self.paths.append(p)
    
    def append(self, *modules):
        for p in self.paths:
            for m in modules:
                p += m

paths = PathManager(process.elPath, process.muPath)


# Filter on the first vertex properties. The produced vertex collection is the same as in [1]
# [1] https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookJetEnergyCorrections#JetEnCorPFnoPU2012
process.goodOfflinePrimaryVertices = cms.EDFilter('FirstVertexFilter',
    src = cms.InputTag('offlineSlimmedPrimaryVertices'),
    cut = cms.string('!isFake & ndof >= 4. & abs(z) < 24. & position.Rho < 2.'))

paths.append(process.goodOfflinePrimaryVertices)


# Define basic reconstructed objects
from Analysis.PECTuples.ObjectsDefinitions_cff import *

eleQualityCuts, eleEmbeddedCutBasedIDLabels, eleCutBasedIDMaps, eleMVAIDMaps = \
 DefineElectrons(process)
muQualityCuts = DefineMuons(process)
recorrectedJetsLabel, jetQualityCuts = DefineJets(process, reapplyJEC = True, runOnData = runOnData)
DefineMETs(process, runOnData = runOnData, jetCollection = recorrectedJetsLabel)


# The loose event selection
process.countTightPatElectrons = cms.EDFilter('PATCandViewCountFilter',
    src = cms.InputTag('patElectronsForEventSelection'),
    minNumber = cms.uint32(1), maxNumber = cms.uint32(999))
process.countTightPatMuons = cms.EDFilter('PATCandViewCountFilter',
    src = cms.InputTag('patMuonsForEventSelection'),
    minNumber = cms.uint32(1), maxNumber = cms.uint32(999))

process.countGoodJets = cms.EDFilter('PATCandViewCountMultiFilter',
    src = cms.VInputTag('analysisPatJets'),
    cut = cms.string('pt > ' + str(jetPtThreshold)),
    minNumber = cms.uint32(minNumJets), maxNumber = cms.uint32(999))
if not runOnData:
    process.countGoodJets.src = cms.VInputTag('analysisPatJets',
        'analysisPatJetsScaleUp', 'analysisPatJetsScaleDown')

if elChan:
    process.elPath += process.countTightPatElectrons
if muChan:
    process.muPath += process.countTightPatMuons
paths.append(process.countGoodJets)


# Apply event filters recommended for analyses involving MET
from Analysis.PECTuples.EventFilters_cff import ApplyEventFilters
ApplyEventFilters(process, paths,
    runOnData = runOnData,
    isPromptReco = options.isPromptReco)


# Save decisions of selected triggers. The lists are aligned with menu [1] used in 25 ns MC and
# menus deployed online
# [1] /frozen/2015/25ns14e33/v1.2/HLT/V2
if runOnData:
    process.pecTrigger = cms.EDFilter('SlimTriggerResults',
        triggers = cms.vstring(
            'Mu45_eta2p1', 'Mu50',
            'IsoMu18', 'IsoMu20', 'IsoTkMu20', 'IsoMu24_eta2p1',
            'Ele23_WPLoose_Gsf', 'Ele27_eta2p1_WPLoose_Gsf'),
        filter = cms.bool(False),
        savePrescales = cms.bool(True),
        triggerBits = cms.InputTag('TriggerResults', processName = 'HLT'),
        triggerPrescales = cms.InputTag('patTrigger'))
else:
    process.pecTrigger = cms.EDFilter('SlimTriggerResults',
        triggers = cms.vstring(
            'Mu45_eta2p1', 'Mu50',
            'IsoMu17_eta2p1', 'IsoMu20', 'IsoTkMu20', 'IsoMu24_eta2p1',
            'Ele22_eta2p1_WP75_Gsf', 'Ele27_eta2p1_WP75_Gsf'),
        filter = cms.bool(False),
        savePrescales = cms.bool(False),
        triggerBits = cms.InputTag('TriggerResults', processName = 'HLT'),
        triggerPrescales = cms.InputTag('patTrigger'))

paths.append(process.pecTrigger)


# Save event ID and basic event content
process.pecEventID = cms.EDAnalyzer('PECEventID')

process.pecElectrons = cms.EDAnalyzer('PECElectrons',
    src = cms.InputTag('analysisPatElectrons'),
    rho = cms.InputTag('fixedGridRhoFastjetAll'),
    effAreas = cms.FileInPath('RecoEgamma/ElectronIdentification/data/Spring15/effAreaElectrons_cone03_pfNeuHadronsAndPhotons_25ns.txt'),
    embeddedBoolIDs = cms.vstring(eleEmbeddedCutBasedIDLabels),
    boolIDMaps = cms.VInputTag(eleCutBasedIDMaps),
    contIDMaps = cms.VInputTag(eleMVAIDMaps),
    selection = eleQualityCuts)

process.pecMuons = cms.EDAnalyzer('PECMuons',
    src = cms.InputTag('analysisPatMuons'),
    selection = muQualityCuts,
    primaryVertices = cms.InputTag('offlineSlimmedPrimaryVertices'))

process.pecJetMET = cms.EDAnalyzer('PECJetMET',
    runOnData = cms.bool(runOnData),
    jets = cms.InputTag('analysisPatJets'),
    jecPayload = cms.string('AK4PFchs'),
    jetMinPt = cms.double(20.),
    jetSelection = jetQualityCuts,
    met = cms.InputTag('slimmedMETs', processName = process.name_()))

process.pecPileUp = cms.EDAnalyzer('PECPileUp',
    primaryVertices = cms.InputTag('offlineSlimmedPrimaryVertices'),
    rho = cms.InputTag('fixedGridRhoFastjetAll'),
    runOnData = cms.bool(runOnData),
    puInfo = cms.InputTag('slimmedAddPileupInfo'))

paths.append(process.pecTrigger, process.pecEventID, process.pecElectrons, process.pecMuons, \
 process.pecJetMET, process.pecPileUp)


# Save global generator information
if not runOnData:
    process.pecGenerator = cms.EDAnalyzer('PECGenerator',
        generator = cms.InputTag('generator'),
        saveLHEWeightVars = cms.bool(options.saveLHEWeightVars),
        lheEventInfoProduct = cms.InputTag('externalLHEProducer'))
    paths.append(process.pecGenerator)


# Save information about the hard interaction and selected particles
if not runOnData and options.saveGenParticles:
    process.pecGenParticles = cms.EDAnalyzer('PECGenParticles',
        genParticles = cms.InputTag('prunedGenParticles'),
        saveExtraParticles = cms.vuint32(6, 23, 24, 25))
    paths.append(process.pecGenParticles)


# Save information on heavy-flavour quarks
# if options.saveHeavyFlavours:
#     process.heavyFlavours = cms.EDAnalyzer('PartonShowerOutcome',
#         absPdgId = cms.vint32(4, 5),
#         genParticles = cms.InputTag('genParticles'))
#     paths.append(process.heavyFlavours)


# Save information on generator-level jets and MET
if not runOnData and options.saveGenJets:
    process.pecGenJetMET = cms.EDAnalyzer('PECGenJetMET',
        jets = cms.InputTag('slimmedGenJets'),
        cut = cms.string('pt > 8.'),  # the pt cut is synchronised with JME-13-005
        saveFlavourCounters = cms.bool(True),
        met = cms.InputTag('slimmedMETs', processName = process.name_()))
    paths.append(process.pecGenJetMET)


# In case one of the channels is not requested for the processing, remove it
if not elChan:
    process.elPath = cms.Path()
if not muChan:
    process.muPath = cms.Path()


# The output file for the analyzers
postfix = '_' + string.join([random.choice(string.letters) for i in range(3)], '')

process.TFileService = cms.Service('TFileService',
    fileName = cms.string(options.outputName + postfix + '.root'))
