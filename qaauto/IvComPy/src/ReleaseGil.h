#ifndef RELEASEGIL_H
#define RELEASEGIL_H

#include <boost/python.hpp>
#include <GSLog.H>

/////////////////////////////////////////
// release GIL before extensive operation
// python thread enter C++, releaseGIL, no python API after the release.
class ReleaseGil {
public:
  ReleaseGil() {
    //GSLOGFDEBUG << "Save/Release GIL" <<endl;
    thread_state_ = PyEval_SaveThread();
  }

  ~ReleaseGil() {
    //GSLOGFDEBUG << "Restore GIL" <<endl;
    PyEval_RestoreThread( thread_state_ );
  }

private:
  PyThreadState *thread_state_;
};

//////////////////////////////////////////
// AquireGIL before call back python
// from C++ thread access python API
class AquireGil {
public:
    AquireGil()
    {
        //GSLOGFDEBUG << "Ensure GIL" <<endl;
        gstate_ = PyGILState_Ensure();
    }
    ~AquireGil()
    {
        //GSLOGFDEBUG << "Release GIL" <<endl;
        PyGILState_Release(gstate_);
    }

private:
    PyGILState_STATE gstate_;

};

#endif /* end of include guard: RELEASEGIL_H_RDIEBSQ1 */

