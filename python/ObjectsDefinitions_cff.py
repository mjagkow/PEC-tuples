""" The module contains definitions of physical objects including required adjustments to the
    reconstruction process. Functions defined here must be called after usePF2PAT, name of the
    modules are hard-coded.
    """


# Metadata
__author__ = 'Andrey Popov'
__email__ = 'Andrey.Popov@cern.ch'


import FWCore.ParameterSet.Config as cms


def DefineElectrons(process, PFRecoSequence, runOnData):
    """ This function adjusts electron reconstruction. Among all the fields being added to the
        process, the user is expected to use the following only:
        
        1. nonIsolatedLoosePatElectrons: maximally loose collection of electrons to be saved in the
        tuples.
        
        2. eleQualityCuts: vector of quality cuts to be applied to the above collection.
        
        3. patElectronsForEventSelection: collection to be exploited for an event selection, 
        contains all the electrons passing a simple pure-kinematic selection.
        
        4. selectedPatElectrons: electrons passing loose cuts in isolation, ID, and kinematics; to
        be used for the MET uncertainty tool.
    """
    
    # Define a module to produce a value map with rho correction of electron isolation. The
    # configuration fragment is copied from [1] because it is not included in the current tag of
    # UserCode/EGamma/EGammaAnalysisTools. General outline of configuration is inspired by [2].
    # [1] http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/UserCode/EGamma/EGammaAnalysisTools/python/electronIsolatorFromEffectiveArea_cfi.py?hideattic=0&revision=1.1.2.2&view=markup
    # [2] https://twiki.cern.ch/twiki/bin/viewauth/CMS/TwikiTopRefHermeticTopProjections?rev=4#Electrons
    # 
    # In both real data and simulation an effective area derived from real data (2012 HCP dataset)
    # is applied. Possible difference between data and simulation is belived to be small [3-4]
    # [3] https://hypernews.cern.ch/HyperNews/CMS/get/top/1607.html
    # [4] https://hypernews.cern.ch/HyperNews/CMS/get/egamma/1263/1/2/1.html
    process.elPFIsoValueEA03 = cms.EDFilter('ElectronIsolatorFromEffectiveArea',
        gsfElectrons = cms.InputTag('gsfElectrons'),
        pfElectrons = cms.InputTag('pfSelectedElectrons'),
        rhoIso = cms.InputTag('kt6PFJets', 'rho'),
        EffectiveAreaType = cms.string('kEleGammaAndNeutralHadronIso03'),
        EffectiveAreaTarget = cms.string('kEleEAData2012'))
    
    
    # Change the isolation cone used in pfIsolatedElectrons to 0.3, as recommended in [1] and [2].
    # The parameter for the delta-beta correction is initialized with the map for the rho correction
    # [1] https://twiki.cern.ch/twiki/bin/view/CMS/EgammaCutBasedIdentification?rev=17#Particle_Flow_Isolation
    # [2] https://twiki.cern.ch/twiki/bin/view/CMS/TWikiTopRefEventSel?rev=178#Electrons
    process.pfIsolatedElectrons.isolationValueMapsCharged = cms.VInputTag(
        cms.InputTag('elPFIsoValueCharged03PFId'))
    process.pfIsolatedElectrons.deltaBetaIsolationValueMap = cms.InputTag('elPFIsoValuePU03PFId')
    process.pfIsolatedElectrons.isolationValueMapsNeutral = cms.VInputTag(
        cms.InputTag('elPFIsoValueNeutral03PFId'), cms.InputTag('elPFIsoValueGamma03PFId'))
    process.pfIsolatedElectrons.deltaBetaIsolationValueMap = cms.InputTag('elPFIsoValueEA03')
    
    PFRecoSequence.replace(process.pfIsolatedElectrons,
     process.elPFIsoValueEA03 * process.pfIsolatedElectrons)
    
    
    # Adjust parameters for the rho correction [1]. The cut on the isolation value is set in
    # accordance with [2]
    # [1] https://twiki.cern.ch/twiki/bin/viewauth/CMS/TwikiTopRefHermeticTopProjections?rev=4#Electrons
    # [2] https://twiki.cern.ch/twiki/bin/view/CMS/TWikiTopRefEventSel?rev=178#Veto
    process.pfIsolatedElectrons.doDeltaBetaCorrection = True
    process.pfIsolatedElectrons.deltaBetaFactor = -1.
    process.pfIsolatedElectrons.isolationCut = 0.15
    
    
    # Apply remaining cuts that define veto electrons as required in [1]. It is implemented via an
    # additional module and not in pfSelectedElectrons, becase all the isolation maps are associated
    # with the latter collection, and they will be needed also for a looser electron selection
    # [1] https://twiki.cern.ch/twiki/bin/view/CMS/TWikiTopRefEventSel?rev=178#Veto
    process.pfElectronsForTopProjection = process.pfSelectedElectrons.clone(
        src = 'pfIsolatedElectrons',
        cut = 'pt > 20. & abs(eta) < 2.5')
    process.pfNoElectron.topCollection = 'pfElectronsForTopProjection'
    
    PFRecoSequence.replace(process.pfIsolatedElectrons,
     process.pfIsolatedElectrons * process.pfElectronsForTopProjection)
    
    
    
    # Collection pfElectronsForTopProjection, which contains isolated and identified electrons
    # passing basic kinematical cuts, is used in the top projections. It should also be
    # provided to the MET uncertainty tool (in case of MC simulated data); however, the latter
    # expects PAT electrons. Since they cannot be constructed from pfElectronsForTopProjection
    # collection (isolation ValueMap issues), they should be subjected to an additional selection.
    
    
    # Load electron MVA ID modules. See an example in [1], which is referenced from [2]
    # [1] http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/CMSSW/EgammaAnalysis/ElectronTools/test/patTuple_electronId_cfg.py?view=markup&pathrev=SE_PhotonIsoProducer_MovedIn
    # [2] https://twiki.cern.ch/twiki/bin/view/CMS/MultivariateElectronIdentification?rev=45#Recipe_for_53X
    process.load('EgammaAnalysis.ElectronTools.electronIdMVAProducer_cfi')
    
    PFRecoSequence.replace(process.patElectrons, process.mvaTrigV0 * process.patElectrons)
    
    # Set an accessor for the MVA ID [1-2]
    # [1] https://twiki.cern.ch/twiki/bin/view/CMS/TWikiTopRefEventSel?rev=178#Electrons
    # [2] http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/UserCode/EGamma/EGammaAnalysisTools/test/patTuple_electronId_cfg.py?revision=1.2&view=markup&pathrev=V00-00-16
    process.patElectrons.electronIDSources = cms.PSet(mvaTrigV0 = cms.InputTag('mvaTrigV0'))
    
    # Change the size of the isolation cone for PAT electrons
    from PhysicsTools.PatAlgos.tools.pfTools import adaptPFIsoElectrons
    adaptPFIsoElectrons(process, process.patElectrons, '', '03')
    
    # Insert the effective-area isolation correction as a user isolation
    process.patElectrons.isolationValues.user = cms.VInputTag(cms.InputTag('elPFIsoValueEA03'))
    
    # Selection to mimic the pfElectronsForTopProjection collection
    process.selectedPatElectrons.cut = '(' + process.pfElectronsForTopProjection.cut.value() + \
     ') & electronID("mvaTrigV0") > 0.'
    
    
    
    # Although the "good" electrons are a subset of the patElectrons collection defined above, it is
    # usefull to save all the electrons in the event (especially for the QCD studies). Duplicate the
    # patElectrons module to perform it
    process.nonIsolatedLoosePatElectrons = process.patElectrons.clone(
        pfElectronSource = 'pfSelectedElectrons')
    
    PFRecoSequence.replace(process.patElectrons, process.patElectrons +
     process.nonIsolatedLoosePatElectrons)
    
    
    
    # The above electron collection will be stored in the produced tuples. It is also needed to save
    # the results of some quality criteria evaluation. Such parameters as pt, eta, isolation,
    # transverse impact-parameter, MVA ID value, and conversion flag are stored in the tuples,
    # whereas other criteria are not. Instead they are encoded in the following selection strings
    eleQualityCuts = cms.vstring(
        '(abs(superCluster.eta) < 1.4442 | abs(superCluster.eta) > 1.5660)')
    
    
    
    # Finally, a collection for the event selection is needed. It is based on pure kinematical
    # properties only (the electron is allowed to be non-isolated or be poorly identified). Note
    # that it is recommended [1] to use momentum of the associated GSF electron
    # [1] https://twiki.cern.ch/twiki/bin/view/CMS/B2GRefEventSel#Isolation_and_Corrections_to_Iso
    process.patElectronsForEventSelection = process.selectedPatElectrons.clone(
        src = 'nonIsolatedLoosePatElectrons',
        cut = 'ecalDrivenMomentum.pt > 27. & (ecalDrivenMomentum.eta < 2.5)')
    
    PFRecoSequence.replace(process.nonIsolatedLoosePatElectrons,
     process.nonIsolatedLoosePatElectrons + process.patElectronsForEventSelection)
    
    
    # Return values
    return eleQualityCuts



def DefineMuons(process, PFRecoSequence, runOnData):
    """ This function adjusts muon reconstruction. The following collections and variables are
        expected to be used by the user:
        
        1. nonIsolatedLoosePatMuons: collection of loose non-isolated muons to be stored in the
        tuples.
        
        2. muQualityCuts: vector of quality cuts to be applied to the above collection.
        
        3. patMuonsForEventSelection: collection of loose non-isolated muons that pass basic
        kinematical requirements; to be used for an event selection.
        
        4. selectedPatMuons: loosely identified and isolated muons, which are expected by the MET
        uncertainty tool.
    """
    
    # Update definition of loose muons to match [1-2]; isolation is addressed later. It needs to be
    # confirmed, but it looks like muonRef().isAvailable() returns true always and is required for
    # consistency only
    # [1] https://twiki.cern.ch/twiki/bin/view/CMS/TWikiTopRefEventSel?rev=178#Muons
    # [2] https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideMuonId?rev=46#Loose_Muon
    process.pfSelectedMuons.cut = 'pt > 10. & abs(eta) < 2.5 & muonRef.isAvailable & '\
     'muonRef.isPFMuon & (muonRef.isGlobalMuon | isTrackerMuon)'
    
    
    # Enable delta-beta correction for the muon isolation and set the recommended cut [1]
    # [1] https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideMuonId?rev=46#Muon_Isolation
    process.pfIsolatedMuons.doDeltaBetaCorrection = True
    process.pfIsolatedMuons.deltaBetaFactor = -0.5
    process.pfIsolatedMuons.isolationCut = 0.2
    
    
    # Tight muons are contained in collection patMuons, which is build from the above collection
    # pfIsolatedMuons, but it is convenient to save also non-isolated muons in order to allow QCD
    # studies. The task is performed with a duplicate of patMuons module
    process.nonIsolatedLooseMuonMatch = process.muonMatch.clone(
        src = 'pfSelectedMuons')
    process.nonIsolatedLoosePatMuons = process.patMuons.clone(
        pfMuonSource = 'pfSelectedMuons',
        genParticleMatch = 'nonIsolatedLooseMuonMatch')
    
    PFRecoSequence.replace(process.patMuons, process.patMuons +
     process.nonIsolatedLooseMuonMatch * process.nonIsolatedLoosePatMuons)
    if runOnData:
        PFRecoSequence.remove(process.nonIsolatedLooseMuonMatch)
    
    
    # The above collection of muons is saved in the tuples. It is needed to store informaion about
    # quality criteria the muons meet. A part of it is encoded in dedicated variables such as pt,
    # eta, isolation, or impact-parameter. The others are included in the selection strings
    # below. They follow recommendations in [1]
    # [1] https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideMuonId?rev=46#The2012Data
    muQualityCuts = cms.vstring(
        # tight muons
        'isPFMuon & isGlobalMuon & globalTrack.normalizedChi2 < 10 & '\
        'globalTrack.hitPattern.numberOfValidMuonHits > 0 & numberOfMatchedStations > 1 & '\
        'innerTrack.hitPattern.numberOfValidPixelHits > 0 & '\
        'track.hitPattern.trackerLayersWithMeasurement > 5')
    
    
    # Finally, a collection for an event selection is needed. It is based on pure kinematical
    # properties only (the muon is allowed to be non-isolated or be poorly identified)
    process.patMuonsForEventSelection = process.selectedPatMuons.clone(
        src = 'nonIsolatedLoosePatMuons',
        cut = 'pt > 17. & abs(eta) < 2.1')
    
    PFRecoSequence.replace(process.nonIsolatedLoosePatMuons,
     process.nonIsolatedLoosePatMuons + process.patMuonsForEventSelection)
    
    
    # Return values
    return muQualityCuts


def DefineJets(process, paths, runOnData):
    """ Adjusts jet reconstruction. The function must be called after the MET uncertainty tool.
        The user is expected to operate with the following collections:
        
        1. analysisPatJets: jets subjected to recommended quality selection; to be used in the
        analysis.
        
        2. patJetsForEventSelection: a hard subset of the above collection needed to perform an
        event selection.
        
        3. selectedPatJets: jets from PFBRECO embedded in pat::Jet class; to be used with the MET
        uncertainty tool.
    """
    
    # Jet identification criteria as recommended in [1-2]
    # [1] https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetID
    # [2] https://hypernews.cern.ch/HyperNews/CMS/get/JetMET/1429.html
    jetQualityCut = 'numberOfDaughters > 1 & '\
     '(neutralHadronEnergy + HFHadronEnergy) / energy < 0.99 & '\
     'neutralEmEnergyFraction < 0.99 & (abs(eta) < 2.4 & chargedEmEnergyFraction < 0.99 & '\
     'chargedHadronEnergyFraction > 0. & chargedMultiplicity > 0 | abs(eta) >= 2.4)'
    
    
    # The collection selectedPatJets encorporates jets reconstructed in the PFBRECO framework; they
    # are used in the MET uncertainty tool
    
    
    # Jets considered in the analysis are subjected to an additional selection
    process.analysisPatJets = process.selectedPatJets.clone(
        src = 'selectedPatJets' if runOnData else 'smearedPatJets',
        cut = 'pt > 10. & abs(eta) < 4.7 & (' + jetQualityCut + ')')
    
    
    # Jets used in the event selection
    process.patJetsForEventSelection = process.analysisPatJets.clone(
        src = 'analysisPatJets',
        cut = 'pt > 30.')
    
    
    paths.append(process.selectedPatJets, process.analysisPatJets, process.patJetsForEventSelection)
    
    
    # Finally, switch on the tag infos. It is needed to access the secondary vertex [1]
    # [1] https://hypernews.cern.ch/HyperNews/CMS/get/physTools/2714/2/1/1.html
    process.patJets.addTagInfos = True
    
    
    # Add PU jet ID [1]
    # [1] https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupJetID
    # WARNING: The package looks quite raw, many adjustments have been made by hand with no official
    # recommendation. This tool should not be used in a physics analysis
    process.load('CMGTools.External.pujetidsequence_cff')
    
    # By default, PU ID is calculated for selectedPatJets, but analysers need it to be associated
    # with collection analysisPatJets
    for m in [process.puJetIdChs, process.puJetMvaChs]:
        m.jets = 'analysisPatJets'
    
    # "Simple" BDT is missing in the default configuration. Add it
    from CMGTools.External.pujetidproducer_cfi import simple_5x_chs
    process.puJetMvaChs.algos.append(simple_5x_chs)
    
    # XML files with configuration of the "full" are resolved from a wrong location. Correct it
    process.puJetMvaChs.algos[0].tmvaWeights = 'CMGTools/External/data/' + \
     process.puJetMvaChs.algos[0].tmvaWeights.value().split('/')[3]
    #^ That is just not to retype file's basename
    
    paths.append(process.puJetIdSqeuenceChs)


def DefineMETs(process, paths, runOnData, jecLevel):
    """ The function adjusts MET reconstruction. The following corrections are included: type-I
        (switched on by PF2PAT function), type-0, and phi-modulation correction.
    """
    
    METCollections = []
    #^ MET collections to store. The first one will be raw PF MET, the second one will include the
    # type-I and type-0 corrections as well as the MET phi-modulation correction. Type-I correction
    # is performed with selectedPatJets collection
    process.load('JetMETCorrections.Type1MET.pfMETsysShiftCorrections_cfi')

    if runOnData:
        METCollections.extend(['patPFMet', 'patMETs'])
        
        # Include the type-0 MET correction. The code is inspired by [1]
        # [1] https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookMetAnalysis#Type_I_II_0_with_PF2PAT
        process.patType1CorrectedPFMet.srcType1Corrections.append(
            cms.InputTag('patPFMETtype0Corr'))
        
        # Correct for MET phi modulation. The code is inspired by the implementation [1] of the
        # runMEtUncertainties tool and [2]
        # [1] http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/CMSSW/PhysicsTools/PatUtils/python/tools/metUncertaintyTools.py?revision=1.25&view=markup
        # [2] https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookMetAnalysis#MET_x_y_Shift_Correction_for_mod
        process.pfMEtSysShiftCorr.parameter = process.pfMEtSysShiftCorrParameters_2012runABCDvsNvtx_data
        process.patType1CorrectedPFMet.srcType1Corrections.append(
            cms.InputTag('pfMEtSysShiftCorr'))
        
        # There is some mismatch between the python configurations and CMSSW plugins in the current
        # setup (*), (**). This is corrected below
        # (*) http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/CMSSW/JetMETCorrections/Type1MET/plugins/SysShiftMETcorrInputProducer.cc?revision=1.2&view=markup
        # (**) http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/CMSSW/JetMETCorrections/Type1MET/plugins/SysShiftMETcorrInputProducer.cc?revision=1.3&view=markup
        process.pfMEtSysShiftCorr.src = process.pfMEtSysShiftCorr.srcMEt
        process.pfMEtSysShiftCorr.parameter = process.pfMEtSysShiftCorr.parameter[0]
        
        # Insert missing modules into the sequence
        process.patPF2PATSequence.replace(process.patType1CorrectedPFMet,
            process.type0PFMEtCorrection + process.patPFMETtype0Corr + \
            process.pfMEtSysShiftCorrSequence + process.patType1CorrectedPFMet)
    
    else:  # in case of MC the runMEtUncertainties tool takes care of the corrections
        METCollections.extend(['patMETs', 'patType1CorrectedPFMet'])
        
        # Produce the corrected MET and perform systematical shifts [1]
        # [1] https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuidePATTools#METSysTools
        from PhysicsTools.PatUtils.tools.metUncertaintyTools import runMEtUncertainties
        runMEtUncertainties(process,
            electronCollection = 'selectedPatElectrons', muonCollection = 'selectedPatMuons',
            tauCollection = '', photonCollection = '', jetCollection = 'selectedPatJets',
            jetCorrLabel = jecLevel,
            makeType1corrPFMEt = True, makeType1p2corrPFMEt = False,
            doApplyType0corr = True, doApplySysShiftCorr = True,
            sysShiftCorrParameter = process.pfMEtSysShiftCorrParameters_2012runABCDvsNvtx_mc[0],
            #dRjetCleaning = -1,  # this parameter is never used by the function
            addToPatDefaultSequence = False, outputModule = '')
        
        # Switch off the lepton-jet cleaning
        del(process.patJetsNotOverlappingWithLeptonsForMEtUncertainty.checkOverlaps.electrons)
        del(process.patJetsNotOverlappingWithLeptonsForMEtUncertainty.checkOverlaps.muons)
        
        # Add systematical variations
        METCollections.extend(['patType1CorrectedPFMetJetEnUp', 'patType1CorrectedPFMetJetEnDown',
            'patType1CorrectedPFMetJetResUp', 'patType1CorrectedPFMetJetResDown',
            'patType1CorrectedPFMetUnclusteredEnUp', 'patType1CorrectedPFMetUnclusteredEnDown',
            'patType1CorrectedPFMetElectronEnUp', 'patType1CorrectedPFMetElectronEnDown',
            'patType1CorrectedPFMetMuonEnUp', 'patType1CorrectedPFMetMuonEnDown'])
        
        # Update files with individual JEC uncertainty sources [1] and correct name of subtotal
        # uncertainty as it is outdated in the default configuraion. There are two files with jet
        # energy corrections and uncertainties: for data and for simulation; the difference
        # originate from L1FastJet corrections [2]
        # [1] https://twiki.cern.ch/twiki/bin/view/CMS/JECUncertaintySources?rev=17#2012_JEC
        # [2] https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookJetEnergyCorrections?rev=115#JetEnCor2012Summer13
        for moduleName in process.metUncertaintySequence.moduleNames():
            module = getattr(process, moduleName)
            if ['jetCorrUncertaintyTag', 'jetCorrInputFileName'] in dir(module):
                module.jetCorrUncertaintyTag = 'SubTotalMC'
                module.jetCorrInputFileName = cms.FileInPath(
                 'UserCode/SingleTop/data/Summer13_V4_MC_Uncertainty_AK5PFchs.txt')
        
        # Correct for the mismatch between the python configurations and CMSSW plugins (similar to
        # the case of the real data above)
        process.pfMEtSysShiftCorr.src = process.pfMEtSysShiftCorr.srcMEt
        
        # Insert modules to perform type-0 and phi-modulation corrections into the sequence (for
        # some reason MET uncertainty tool does not do it automatically)
        process.metUncertaintySequence.replace(process.patType1CorrectedPFMet,
            process.type0PFMEtCorrection + process.patPFMETtype0Corr + process.pfMEtSysShiftCorr + \
            process.patType1CorrectedPFMet)
        #^ Some collections are created several times under different names (good primary vertices,
        # for example), but it should not impose a significant overhead
        
        paths.append(process.metUncertaintySequence)
    
    # Return the list of produced collections
    return METCollections

