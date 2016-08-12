#ifndef RELEASEGIL_H
#define RELEASEGIL_H

#include <boost/python.hpp>

/////////////////////////////////////////
// release GIL before extensive operation
//
class ReleaseGil {
public:
  ReleaseGil() {
    thread_state_ = PyEval_SaveThread();
  }

  ~ReleaseGil() {
    PyEval_RestoreThread( thread_state_ );
  }

private:
  PyThreadState *thread_state_;
};

//////////////////////////////////////////
// AquireGIL before call back python
// from C++ thread
class AquireGil {
public:
    AquireGil()
    {
        gstate_ = PyGILState_Ensure();
    }
    ~AquireGil()
    {
        PyGILState_Release(gstate_);
    }

private:
    PyGILState_STATE gstate_;

};

#endif /* end of include guard: RELEASEGIL_H_RDIEBSQ1 */

