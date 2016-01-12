#include "LHEEventWeights.h"

#include <FWCore/Utilities/interface/InputTag.h>
#include <FWCore/Framework/interface/MakerMacros.h>

#include <fstream>
#include <iostream>
#include <iomanip>


using namespace edm;
using namespace std;


LHEEventWeights::LHEEventWeights(ParameterSet const &cfg):
    weightsHeaderTag(cfg.getParameter<string>("weightsHeaderTag")),
    computeMeanWeights(cfg.getParameter<bool>("computeMeanWeights")),
    storeWeights(cfg.getParameter<bool>("storeWeights")),
    printToFiles(cfg.getParameter<bool>("printToFiles")),
    nEventsProcessed(0),
    bfAltWeights(nullptr)
{
    // Register required input data
    lheRunInfoToken =
     consumes<LHERunInfoProduct, edm::InRun>(cfg.getParameter<InputTag>("lheRunInfoProduct"));
    //^ See here [1] about reading data from a run
    //[1] https://hypernews.cern.ch/HyperNews/CMS/get/edmFramework/3583/1.html
    lheEventInfoToken =
     consumes<LHEEventProduct>(cfg.getParameter<InputTag>("lheEventInfoProduct"));
}


LHEEventWeights::~LHEEventWeights()
{
    delete [] bfAltWeights;
}


void LHEEventWeights::fillDescriptions(ConfigurationDescriptions &descriptions)
{
    ParameterSetDescription desc;
    desc.add<InputTag>("lheRunInfoProduct")->setComment("Tag to access per-run LHE information.");
    desc.add<string>("weightsHeaderTag", "initrwgt")->
     setComment("Tag to identify LHE header with description of event weights.");
    desc.add<InputTag>("lheEventInfoProduct")->
     setComment("Tag to access per-event LHE information.");
    desc.add<bool>("computeMeanWeights", true)->
     setComment("Indicates whether mean values of all weights should be computed.");
    desc.add<bool>("storeWeights", false)->
     setComment("Indicates whether event weights should be stored in a ROOT tree.");
    desc.add<bool>("printToFiles", false)->
     setComment("Indicates whether the output should be stored in text files or printed to cout.");
    
    descriptions.add("lheEventWeights", desc);
}


void LHEEventWeights::analyze(Event const &event, EventSetup const &)
{
    // Read LHE information for the current event
    Handle<LHEEventProduct> lheEventInfo;
    event.getByToken(lheEventInfoToken, lheEventInfo);
    
    
    // The nominal weight
    double const nominalWeight = lheEventInfo->originalXWGTUP();
    
    // Vector of alternative weights (e.g. systematic variations)
    vector<gen::WeightsInfo> const &altWeights = lheEventInfo->weights();
    
    
    // Perform initialization when processing the first event
    if (nEventsProcessed == 0)
    {
        if (computeMeanWeights)
            SetupWeightMeans(altWeights);
        
        if (storeWeights)
            SetupWeightTree(altWeights.size());
    }
    
    
    // Update means if requested
    if (computeMeanWeights)
    {
        // Use online algorithm described here [1]
        //[1] https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
        meanWeights.front().second +=
         (nominalWeight - meanWeights.front().second) / (nEventsProcessed + 1);
        
        for (unsigned i = 0; i < altWeights.size(); ++i)
        {
            meanWeights.at(i + 1).second +=
             (altWeights.at(i).wgt - meanWeights.at(i + 1).second) / (nEventsProcessed + 1);
        }
    }
    
    
    // Fill the output tree if requested
    if (storeWeights)
    {
        bfNominalWeight = nominalWeight;
        bfNumAltWeights = altWeights.size();
        
        for (unsigned i = 0; i < altWeights.size(); ++i)
            bfAltWeights[i] = altWeights.at(i).wgt;
        
        
        outTree->Fill();
    }
    
    
    // Update event counter
    ++nEventsProcessed;
}


void LHEEventWeights::endRun(Run const &run, EventSetup const &)
{
    // Create the output stream. Depending on the value of the printToFiles flag, it is either the
    //standard output or a file
    std::streambuf *buf;
    std::ofstream outFile;
    
    if (printToFiles)
    {
        outFile.open("weightsInfo.txt");
        buf = outFile.rdbuf();
    }
    else
        buf = std::cout.rdbuf();
    
    std::ostream out(buf);
    
    
    // Read LHE header
    Handle<LHERunInfoProduct> lheRunInfo;
    run.getByToken(lheRunInfoToken, lheRunInfo);
    
    
    // The header is split in LHERunInfoProduct into several blocks also called "headers". Loop over
    //them and find the one that contains descriptions of event weights
    for (auto header = lheRunInfo->headers_begin(); header != lheRunInfo->headers_end(); ++header)
    {
        // Skip all "headers" except for the sought-for one
        if (header->tag() != weightsHeaderTag)
            continue;
        
        // Print the header to the selected output stream
        for (auto const &l: header->lines())
            out << l;
    }
}


void LHEEventWeights::endJob()
{
    // Create the output stream. Depending on the value of the printToFiles flag, it is either the
    //standard output or a file
    std::streambuf *buf;
    std::ofstream outFile;
    
    if (printToFiles)
    {
        outFile.open("meanWeights.txt");
        buf = outFile.rdbuf();
    }
    else
        buf = std::cout.rdbuf();
    
    std::ostream out(buf);
    
    
    // Print mean values of weights into the selected output stream
    out << "Mean values of event weights:\n index   ID   mean\n\n";
    out.precision(10);
    out << "   -   nominal   " << meanWeights.front().second << "\n\n";
    
    for (unsigned i = 1; i < meanWeights.size(); ++i)
    {
        auto const &w = meanWeights.at(i);
        out << " " << setw(3) << i - 1 << "   " << w.first << "   " << w.second << '\n';
    }
    
    out << endl;
}


void LHEEventWeights::SetupWeightMeans(vector<gen::WeightsInfo> const &altWeights)
{
    meanWeights.reserve(1 + altWeights.size());
    
    
    // Set text IDs for all weights and set their means to zeros
    meanWeights.emplace_back("nominal", 0.);
    
    for (auto const &w: altWeights)
        meanWeights.emplace_back(w.id, 0.);
}


void LHEEventWeights::SetupWeightTree(unsigned nAltWeights)
{
    // Allocate a buffer to store alternative weights
    bfNumAltWeights = nAltWeights;
    bfAltWeights = new Float_t[nAltWeights];
    
    
    // Create the tree and setup its branches
    outTree = fileService->make<TTree>("EventWeights", "Generator-level event weights");
    
    outTree->Branch("nominalWeight", &bfNominalWeight);
    outTree->Branch("numAltWeights", &bfNumAltWeights);
    outTree->Branch("altWeights", bfAltWeights, "altWeights[numAltWeights]/F");
}


DEFINE_FWK_MODULE(LHEEventWeights);
