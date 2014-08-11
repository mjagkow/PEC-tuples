#pragma once

#include <UserCode/SingleTop/interface/Candidate.h>


namespace pec
{
    /**
     * \class GenParticle
     * \author Andrey Popov
     * \brief Minimalistic discription of a generator-level particle
     * 
     * The PDG ID is stored in a one-byte variable, thus the class is suitable only to store
     * fundamental particles and cannot accommodate, e.g., for all possible hadrons. The user is
     * expected to use a small filtered collection of particles; the mother indices correspond to
     * positions in this filtered collection.
     */
    class GenParticle: public Candidate
    {
    public:
        /// Constructor with no parameters
        GenParticle();
        
        /// Copy constructor
        GenParticle(GenParticle const &src);
        
        /// Assignment operator
        GenParticle &operator=(GenParticle const &src);
        
    public:
        /// Resets the object to a state right after the default initialisation
        virtual void Reset();
        
        /**
         * \brief Sets PDG ID
         * 
         * If the given ID cannot be stored in Char_t, an exception is thrown.
         */
        void SetPdgId(long pdgId);
        
        /**
         * \brief Sets index of the first mother
         * 
         * The index must follow requirements specified in the documentation of the method
         * FirstMotherIndex.
         */
        void SetFirstMotherIndex(int index);
        
        /**
         * \brief Sets index of the last mother
         * 
         * The index must follow requirements specified in the documentation of the method
         * LastMotherIndex.
         */
        void SetLastMotherIndex(int index);
        
        /// Returns PDG ID
        long PdgId() const;
        
        /**
         * \brief Returns index of the first mother
         * 
         * Valid indices start from zero; (-1) indicates that there is no mother in the list. Note
         * that the index correponds to a position in the trimmed list of generator particles, not
         * the orginal genParticles collection in an EDM event.
         */
        int FirstMotherIndex() const;
        
        /**
         * \brief Returns index of the last mother
         * 
         * See documentation for the method FirstMotherIndex. The returned value is expected to
         * differ from (-1) if only the particle has more than one mother.
         */
        int LastMotherIndex() const;
        
    private:
        /// PDG ID
        Char_t pdgId;
        
        /**
         * \brief Indices of the first and the last mother of the particle
         * 
         * Normally, one would use a collection of generator-level particles. These indices
         * correspond to position in this collection, not in the orignal collection genParticles in
         * an EDM event. Indices start from 1, and 0 is reserved to indicate thate the stored
         * collection does not contain the mother (but the getter subtracts 1, so that normal
         * indices start from zero, and the special value is assigned to (-1)). The lastMotherIndex
         * is non-zero if only the particle has more that one mother.
         */
        UChar_t firstMotherIndex, lastMotherIndex;
    };
}