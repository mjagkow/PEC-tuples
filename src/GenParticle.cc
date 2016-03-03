#include <Analysis/PECTuples/interface/GenParticle.h>

#include <stdexcept>
/**/#include <iostream>


pec::GenParticle::GenParticle():
    pdgId(0),
    firstMotherIndex(0), lastMotherIndex(0)
{}


pec::GenParticle::GenParticle(GenParticle const &src):
    Candidate(src),
    pdgId(src.pdgId),
    firstMotherIndex(src.firstMotherIndex), lastMotherIndex(src.lastMotherIndex)
{}


pec::GenParticle &pec::GenParticle::operator=(GenParticle const &src)
{
    Candidate::operator=(src);
    
    pdgId = src.pdgId;
    firstMotherIndex = src.firstMotherIndex;
    lastMotherIndex = src.lastMotherIndex;
    
    return *this;
}


void pec::GenParticle::Reset()
{
    Candidate::Reset();
    
    pdgId = 0;
    firstMotherIndex = lastMotherIndex = 0;
}


void pec::GenParticle::SetPdgId(long pdgId_)
{
    if (std::abs(pdgId_) > 30000)
    {
        // Protect against overflow
        pdgId = ((pdgId_ > 0) ? 30000 : -30000) + pdgId_ % 1000;
    }
    else
        pdgId = pdgId_;
}


void pec::GenParticle::SetFirstMotherIndex(int index)
{
    if (index < -1)
        throw std::runtime_error("GenParticle::SetFirstMotherIndex: Illegal index.");
    
    firstMotherIndex = index + 1;
}


void pec::GenParticle::SetLastMotherIndex(int index)
{
    if (index < -1)
        throw std::runtime_error("GenParticle::SetFirstMotherIndex: Illegal index.");
    
    lastMotherIndex = index + 1;
}


long pec::GenParticle::PdgId() const
{
    return pdgId;
}


int pec::GenParticle::FirstMotherIndex() const
{
    return firstMotherIndex - 1;
}


int pec::GenParticle::LastMotherIndex() const
{
    return lastMotherIndex - 1;
}
