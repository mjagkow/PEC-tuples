/**
 * \author Andrey Popov
 *
 * The plugin saves all the necessary information from the event to a set of flat ROOT trees. It
 * takes all the basic objects: charged leptons, jets, METs. User can specify arbitrary string-based
 * selection for the leptons and jets; it is not used to filter the collection but it is evaluated
 * and the result saved to the tuples as the array of boolean values. Additionally two types of
 * filtering selection for the jets are provided. The parameter 'jetCut' defines which jets are
 * saved to the file. If a jet fails this selection but passes 'softJetCut' it is accounted for in
 * the integral soft jet characteristics of the event. If a jet fails the both filtering selections
 * it is completely ignored. The user is allowed to specify an arbitrary number of alternative METs
 * which is useful to store the MET systematics.
 * 
 * When running on simulation the input jets are supposed to be smeared properly in order to
 * reproduce the jet resolution in data. The plugin takes two additional jet collections
 * corresponding to the JER systematic variation (they are not read for the data). JER variations
 * as well as the JEC uncertainties splitted by stat. independent sources are saved for the
 * simulation.
 * 
 * The basic generator information is saved when available. It includes processID, PDF info, jet
 * flavours, PU information. When requested by 'saveFinalMEState' flag the PDG ID of the particles
 * in the final state of ME are saved. It was tested to provide the reasonable results for POWHEG
 * and MG.
 */


#pragma once

#include <FWCore/Framework/interface/EDAnalyzer.h>
#include <FWCore/Framework/interface/Event.h>
#include <FWCore/ParameterSet/interface/ParameterSet.h>
#include <FWCore/ParameterSet/interface/FileInPath.h>
#include <FWCore/Utilities/interface/InputTag.h>

#include <CondFormats/JetMETObjects/interface/JetCorrectionUncertainty.h>

#include <FWCore/ServiceRegistry/interface/Service.h>
#include <CommonTools/UtilAlgos/interface/TFileService.h>

#include <TTree.h>

#include <string>
#include <vector>


using edm::InputTag;
using std::string;
using std::vector;


class PlainEventContent: public edm::EDAnalyzer
{
    public:
        PlainEventContent(edm::ParameterSet const &cfg);
        ~PlainEventContent();
    
    private:
        void beginJob();
        void endJob();
        void beginRun(edm::Run const &run, edm::EventSetup const &setup);
        void endRun(edm::Run const &run, edm::EventSetup const &setup);
        void analyze(edm::Event const &event, edm::EventSetup const &setup);
        
        // The source collections
        InputTag const eleSrc, muSrc, jetSrc;
        vector<InputTag> const metSrc;
        // String-based selection of the jets to be saved in the tuples
        string const jetCut;
        // String-based selection of the jets to be treated as "soft"
        string const softJetCut;
        // String-based selection which result is stored with the objects (not used for filtering)
        vector<string> const eleSelection, muSelection, jetSelection;
        bool const runOnData;    // indicated whether generator info is availible
        bool const saveHardInteraction;  // whether to save info on status-3 particles
        
        /// Determines if integral properties for soft jets should be saved
        bool const saveIntegralSoftJets;
        
        // Generator information sources. They are not read for real data
        InputTag const generatorSrc, genParticlesSrc;
        InputTag const primaryVerticesSrc;  // collection of reconstructed PV
        InputTag const puSummarySrc;  // PU information. Not read for real data
        InputTag const rhoSrc;  // rho (mean energy density)
        
        
        vector<InputTag> jerSystJetsSrc;  // JER systematic shifted collections of jets
                
        edm::Service<TFileService> fs;  // object providing interface to the ROOT files
        JetCorrectionUncertainty *jecUncProvider;  // object to access the JEC uncertainty
        
        
        /// Maximal size to allocate buffer arrays
        static unsigned const maxSize = 64;
        
        
        // The tree to store the event ID information
        TTree *eventIDTree;
        
        ULong64_t runNumber, lumiSection, eventNumber;
        
        
        // The tree to store the basic kinematics, quality requirements, etc.
        TTree *basicInfoTree;
        
        UChar_t eleSize;  // actual size of the electron collection
        Float_t elePt[maxSize];    // electron 4-momenta
        Float_t eleEta[maxSize];   //
        Float_t elePhi[maxSize];   //
        //Float_t eleMass[maxSize];  // it equals (0 +- 0.03) GeV, can be assumed the PDG value
        Bool_t eleCharge[maxSize];  // electron's charge (true for electron, false for positron)
        Float_t eleDB[maxSize];  // impact-parameter in the transverse plane
        Float_t eleRelIso[maxSize];  // relative isolation
        
        // Trigger-emulating preselection required for triggering MVA ID [1-2]
        //[1] https://twiki.cern.ch/twiki/bin/view/CMS/MultivariateElectronIdentification#Training_of_the_MVA
        //[2] https://hypernews.cern.ch/HyperNews/CMS/get/egamma-elecid/72.html
        Bool_t eleTriggerPreselection[maxSize];
        
        // Electron MVA ID [1]
        //[1] https://twiki.cern.ch/twiki/bin/view/CMS/TWikiTopRefEventSel?rev=178#Electrons
        Float_t eleMVAID[maxSize];
        
        // Old cut-based electron ID [1]
        //[1] https://twiki.cern.ch/twiki/bin/view/CMS/SimpleCutBasedEleID
        UChar_t eleIDSimple70cIso[maxSize];
        
        Bool_t elePassConversion[maxSize];  // conversion veto (true for good electrons)
        Bool_t **eleSelectionBits;  // results of the additional selection
        
        UChar_t muSize;  // actual size of the muon collection
        Float_t muPt[maxSize];    // muon 4-momenta
        Float_t muEta[maxSize];   //
        Float_t muPhi[maxSize];   //
        //Float_t muMass[maxSize];  // it equals (0.106 +- 0.03) GeV, can be assumed the PDG value
        Bool_t muCharge[maxSize];  // muon's charge (true for muon, false for anti-muon)
        Float_t muDB[maxSize];  // impact-parameter in the transverse plane
        Float_t muRelIso[maxSize];  // relative isolation
        Bool_t muQualityTight[maxSize];  // quality cuts to define tight muons
        Bool_t **muSelectionBits;  // results of the additional selection
        
        UChar_t jetSize;  // actual size of the jet collection
        Float_t jetPt[maxSize];    // jet corrected 4-momenta
        Float_t jetEta[maxSize];   //
        Float_t jetPhi[maxSize];   //
        Float_t jetMass[maxSize];  //
        Float_t jecUncertainty[maxSize];  // JEC uncertainty
        
        // JER systematics. The components of 4-momentum are scaled simultaneously (*). Therefore
        //phi and eta are not affected and are the same as for the nominal jets
        //(*) http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/CMSSW/PhysicsTools/PatUtils/interface/SmearedJetProducerT.h?view=markup, function produce()
        Float_t jetPtJERUp[maxSize];
        Float_t jetMassJERUp[maxSize];
        Float_t jetPtJERDown[maxSize];
        Float_t jetMassJERDown[maxSize];
        
        Float_t jetTCHP[maxSize];  // b-tagging discriminators
        Float_t jetCSV[maxSize];   //
        Float_t jetSecVertexMass[maxSize];  // mass of the secondary vertex (a'la SHyFT)
        
        // Electric charge of the jet
        //It simply copies the value returned by pat::Jet::jetCharge(), which is calculated as a sum
        //of electric charges of the jet's contituents weighted with their pt, as mentioned in [1].
        //Note, however, that other definitions are possible [2].
        //[1] https://hypernews.cern.ch/HyperNews/CMS/get/JetMET/1425.html
        //[2] http://arxiv.org/abs/1209.2421
        Float_t jetCharge[maxSize];
        
        // Jet pull angle (radians)
        //The pull vector is defined in [1], Eq. (3.7). The pull angle is an angle between this
        //vector and the rapidity axis
        //[1] http://arxiv.org/abs/1010.3698
        Float_t jetPullAngle[maxSize];
        
        Bool_t **jetSelectionBits;  // results of the additional selection
        
        UChar_t metSize;  // number of different METs stored in the event
        Float_t metPt[maxSize];   // MET absolute value
        Float_t metPhi[maxSize];  // MET phi
        
        
        // The tree to store the integral event characteristics
        TTree *integralPropTree;
        
        // The soft jets
        Float_t softJetPt;
        Float_t softJetEta;
        Float_t softJetPhi;
        Float_t softJetMass;
        Float_t softJetHt;
        
        // The soft jets JEC uncertainties. The weighted sum unc_i * p4_i, where i indexes the jets,
        //is sufficient
        Float_t softJetPtJECUnc;
        Float_t softJetEtaJECUnc;
        Float_t softJetPhiJECUnc;
        Float_t softJetMassJECUnc;
        Float_t softJetHtJECUnc;
        
        // The soft jets JER systematics
        Float_t softJetPtJERUp;
        Float_t softJetEtaJERUp;
        Float_t softJetPhiJERUp;
        Float_t softJetMassJERUp;
        Float_t softJetHtJERUp;
        
        Float_t softJetPtJERDown;
        Float_t softJetEtaJERDown;
        Float_t softJetPhiJERDown;
        Float_t softJetMassJERDown;
        Float_t softJetHtJERDown;
        
        
        // The tree to store generator information (except for one stored in basicInfoTree). It is
        //filled if only runOnData is false, otherwise the tree is not event stored in the file
        TTree *generatorTree;
        
        Short_t processID;  // the generator process ID
        Float_t genWeight;  // the generator weight for the event
        
        Char_t jetFlavour[maxSize];  // algorithmic jet flavour definition
        Char_t jetGenPartonFlavour[maxSize];  // flavour of the parton matched to jet (0 if no match)
        //^ See here (*) for the motivation of using the both flavour definitions
        //(*) https://hypernews.cern.ch/HyperNews/CMS/get/b2g-selections/103.html
                
        Float_t pdfX1, pdfX2;  // momenta fraction carried by initial-state partons
        Float_t pdfQ;  // scale used to evaluate PDF
        Char_t pdfId1, pdfId2;  // ID of the initial-state partons
        
        // Information about the hard interaction (status-3 particles). The initial section (i.e.
        //the first 6 entries in genParticles) is skipped
        UChar_t hardPartSize;  // number of the saved particles
        Char_t hardPartPdgId[maxSize];  // their PDG ID
        Char_t hardPartFirstMother[maxSize], hardPartLastMother[maxSize];  // indices of mothers
        Float_t hardPartPt[maxSize];    // 4-momenta of the particles
        Float_t hardPartEta[maxSize];   //
        Float_t hardPartPhi[maxSize];   //
        Float_t hardPartMass[maxSize];  //
        
        
        // The tree to store pile-up information
        TTree *puTree;
        
        UChar_t pvSize;  // number of primary vertices
        Float_t puRho;  // mean energy density
        Float_t puTrueNumInteractions;  // true mean number of PU interactions in the event
        UChar_t puSize;  // number of stored pile-up bunch crossings
        Char_t puBunchCrossing[maxSize];  // indices for the bunch crossings
        UChar_t puNumInteractions[maxSize];  // number of PU interactions in each crossing
};
